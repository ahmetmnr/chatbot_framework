from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator, Optional, Dict
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.models import Assistant as AssistantModel, Conversation, Message, User
from core.database import get_db
from api.schemas import AssistantResponse, AssistantCreate, ConversationResponse, MessageResponse
from core.services.openai_service import OpenAIService
from core.services.ollama_service import OllamaService
from core.models.assistant import Assistant as AssistantClass
from api.dependencies import get_current_user
import uuid
from datetime import datetime
import os
import json

# Global assistants dictionary
assistants: Dict[str, AssistantClass] = {}

router = APIRouter(
    prefix="/assistants",
    tags=["assistants"]
)

@router.get("/list", response_model=List[AssistantResponse])
async def list_assistants(db: AsyncSession = Depends(get_db)):
    try:
        print("Fetching assistants from database...")
        query = select(AssistantModel)
        result = await db.execute(query)
        db_assistants = result.scalars().all()
        print(f"Found {len(db_assistants)} assistants")
        
        response_list = []
        for assistant in db_assistants:
            try:
                print(f"Processing assistant: {assistant.name}")
                print(f"Assistant data: {assistant.__dict__}")
                
                config = assistant.config if isinstance(assistant.config, dict) else {}
                response = AssistantResponse(
                    id=assistant.id,
                    name=assistant.name,
                    model_type=assistant.model_type,
                    system_message=assistant.system_message,
                    config=config,
                    created_at=assistant.created_at,
                    updated_at=assistant.updated_at,
                    creator_id=assistant.creator_id
                )
                response_list.append(response)
            except Exception as e:
                print(f"Error processing assistant {assistant.name}: {str(e)}")
                continue
        
        return response_list
        
    except Exception as e:
        print(f"Error in list_assistants: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{assistant_name}/chat/stream")
async def chat_stream(
    assistant_name: str,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Önce test kullanıcısını kontrol et/oluştur
        test_user_id = "test-user-id"
        query = select(User).where(User.id == test_user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Test kullanıcısı yoksa oluştur
            user = User(
                id=test_user_id,
                username="test_user",
                email="test@example.com"
            )
            db.add(user)
            await db.commit()
        
        # Asistanı bul
        query = select(AssistantModel).where(AssistantModel.name == assistant_name)
        result = await db.execute(query)
        assistant = result.scalar_one_or_none()
        
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        # Yeni konuşma oluştur
        conversation = Conversation(
            id=str(uuid.uuid4()),
            assistant_id=assistant.id,
            session_id=str(uuid.uuid4()),
            user_id=test_user_id,  # Test kullanıcısını kullan
            created_at=datetime.utcnow()
        )
        
        db.add(conversation)
        await db.commit()
        
        # Kullanıcı mesajını kaydet
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=message,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        await db.commit()

        # Memory'de asistan var mı kontrol et ve oluştur
        if assistant_name not in assistants:
            config = assistant.config if isinstance(assistant.config, dict) else {}
            
            try:
                if assistant.model_type == "openai":
                    model = OpenAIService()
                elif assistant.model_type == "ollama":
                    model = OllamaService()
                else:
                    raise HTTPException(status_code=400, detail="Invalid model type")
                
                assistant = AssistantClass(
                    name=assistant.name,
                    model=model,
                    system_message=assistant.system_message,
                    config=config
                )
                assistants[assistant_name] = assistant
            except Exception as e:
                print(f"Model initialization error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to initialize model: {str(e)}")

        async def generate() -> AsyncGenerator[str, None]:
            full_response = ""
            try:
                async for chunk in assistants[assistant_name].process_message(message, stream=True):
                    if chunk:
                        full_response += chunk
                        yield f"data: {chunk}\n\n"
                
                if full_response:  # Sadece yanıt varsa kaydet
                    assistant_message = Message(
                        id=str(uuid.uuid4()),
                        conversation_id=conversation.id,
                        role="assistant",
                        content=full_response,
                        created_at=datetime.utcnow()
                    )
                    db.add(assistant_message)
                    await db.commit()
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_msg = f"Stream generation error: {str(e)}"
                print(error_msg)
                # Hata mesajını kaydet
                error_message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation.id,
                    role="assistant",
                    content=f"Error: {str(e)}",
                    created_at=datetime.utcnow()
                )
                db.add(error_message)
                await db.commit()
                yield f"data: error: {str(e)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Conversation-Id": str(conversation.id)
            }
        )

    except Exception as e:
        print(f"Chat stream error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create", response_model=AssistantResponse)
async def create_assistant(
    assistant: AssistantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Auth sistemi eklenince
):
    try:
        print(f"Creating assistant: {assistant.name}")
        
        # Önce aynı isimde asistan var mı kontrol et
        query = select(AssistantModel).where(AssistantModel.name == assistant.name)
        result = await db.execute(query)
        existing_assistant = result.scalar_one_or_none()
        
        if existing_assistant:
            raise HTTPException(
                status_code=400,
                detail=f"Assistant with name '{assistant.name}' already exists"
            )
        
        # Yeni asistanı oluştur
        current_time = datetime.utcnow()
        db_assistant = AssistantModel(
            id=str(uuid.uuid4()),
            name=assistant.name,
            model_type=assistant.model_type,
            system_message=assistant.system_message,
            config=assistant.config,
            created_at=current_time,
            updated_at=current_time,
            creator_id=current_user.id  # Kullanıcı ID'sini ekle
        )
        
        db.add(db_assistant)
        await db.commit()
        await db.refresh(db_assistant)
        
        print(f"Assistant created successfully: {db_assistant.name}")
        
        return db_assistant
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in create_assistant: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id",  # Şimdilik test kullanıcısı
    skip: int = 0,
    limit: int = 10
):
    try:
        print(f"Fetching conversations for user: {user_id}")
        
        # Konuşmaları tarihe göre sırala (en yeniden en eskiye)
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        response_list = []
        for conv in conversations:
            # Her konuşmanın mesajlarını al
            messages_query = (
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at.asc())
            )
            messages_result = await db.execute(messages_query)
            messages = messages_result.scalars().all()
            
            # Assistant bilgisini al
            assistant_query = select(AssistantModel).where(AssistantModel.id == conv.assistant_id)
            assistant_result = await db.execute(assistant_query)
            assistant = assistant_result.scalar_one_or_none()
            
            response_list.append(
                ConversationResponse(
                    id=conv.id,
                    assistant_id=conv.assistant_id,
                    assistant_name=assistant.name if assistant else "Unknown",
                    session_id=conv.session_id,
                    user_id=conv.user_id,
                    created_at=conv.created_at,
                    messages=[
                        MessageResponse(
                            id=msg.id,
                            conversation_id=msg.conversation_id,
                            role=msg.role,
                            content=msg.content,
                            created_at=msg.created_at
                        ) for msg in messages
                    ]
                )
            )
        
        return response_list
        
    except Exception as e:
        print(f"Error fetching conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc())
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return messages
        
    except Exception as e:
        print(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Önce mesajları sil
        await db.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        
        # Sonra konuşmayı sil
        result = await db.execute(
            delete(Conversation).where(Conversation.id == conversation_id)
        )
        
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error deleting conversation: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 