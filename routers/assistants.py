from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator, Optional, Dict
from sqlalchemy import select, delete, and_
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
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from sqlalchemy.exc import IntegrityError

# Global (in-memory) Assistants Dictionary
assistants: Dict[str, AssistantClass] = {}

router = APIRouter(
    prefix="/assistants",
    tags=["assistants"]
)


@router.get("/list", response_model=List[AssistantResponse])
async def list_assistants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Veritabanındaki tüm asistanları listeler."""
    try:
        print(f"Fetching assistants for user: {current_user.id}")
        query = select(AssistantModel)
        result = await db.execute(query)
        db_assistants = result.scalars().all()
        return [AssistantResponse.from_orm(assistant) for assistant in db_assistants]
    except Exception as e:
        print(f"Error in list_assistants: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assistant_name}/chat/stream")
async def chat_stream(
    assistant_name: str,
    message: str,
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Streaming endpoint (SSE) ile asistan sohbeti.
    conversation_id verilirse o konuşmaya devam eder,
    verilmezse yeni bir Conversation kaydı oluşturur.
    """
    try:
        # 1. Asistanı DB'den bul
        query = select(AssistantModel).where(AssistantModel.name == assistant_name)
        result = await db.execute(query)
        db_assistant = result.scalar_one_or_none()
        if not db_assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")

        # 2. Mevcut conversation varsa bul
        if conversation_id:
            conv_query = select(Conversation).where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == current_user.id
                )
            )
            conv_result = await db.execute(conv_query)
            conversation = conv_result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # conversation_id yok => yeni bir conversation başlat
            conversation = Conversation(
                id=str(uuid.uuid4()),
                name=f"Chat with {assistant_name}",
                assistant_id=db_assistant.id,
                session_id=str(uuid.uuid4()),
                user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

        # 3. Kullanıcı mesajını DB'ye kaydet
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=message,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        await db.commit()

        # 4. Bellekte asistan var mı? Yoksa oluştur.
        if assistant_name not in assistants:
            config = db_assistant.config if isinstance(db_assistant.config, dict) else {}
            if db_assistant.model_type == "openai":
                model = OpenAIService(model=db_assistant.model_name)
            elif db_assistant.model_type == "ollama":
                model = OllamaService(model=db_assistant.model_name)
            else:
                raise HTTPException(status_code=400, detail="Invalid model type")

            new_assistant = AssistantClass(
                name=db_assistant.name,
                model=model,
                system_message=db_assistant.system_message,
                config=config
            )
            assistants[assistant_name] = new_assistant

        # 5. Yanıtı stream şeklinde döndüren generator
        async def generate() -> AsyncGenerator[str, None]:
            full_response = ""
            try:
                # Asistan objesini memory'den al
                current_assistant = assistants[assistant_name]

                # Asistan yanıtını parça parça al
                async for chunk in current_assistant.process_message(message, stream=True):
                    if chunk:
                        full_response += chunk
                        yield f"data: {chunk}\n\n"

                # Yanıt tamamlanınca asistan mesajını kaydet
                if full_response:
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

                # Hata mesajını DB'ye de kaydedebiliriz
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

        # 6. SSE response
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "X-Conversation-Id": str(conversation.id),
                "Cache-Control": "no-cache"
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
    current_user: User = Depends(get_current_user)
):
    try:
        # Model servisini oluştur
        if assistant.model_type == "openai":
            model_service = OpenAIService(model=assistant.model_name)
        elif assistant.model_type == "ollama":
            model_service = OllamaService(model=assistant.model_name)
        else:
            raise HTTPException(status_code=400, detail="Invalid model type")
        
        # Veritabanına kaydet
        db_assistant = AssistantModel(
            id=str(uuid.uuid4()),
            name=assistant.name,
            model_type=assistant.model_type,
            model_name=assistant.model_name,
            system_message=assistant.system_message,
            config=assistant.config,
            creator_id=current_user.id
        )
        db.add(db_assistant)
        await db.commit()
        await db.refresh(db_assistant)
        
        # Asistanı memory'ye ekle
        new_assistant = AssistantClass(
            name=assistant.name,
            model=model_service,
            system_message=assistant.system_message,
            config=assistant.config
        )
        assistants[assistant.name] = new_assistant
        
        return db_assistant
        
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Assistant name already exists"
        )
    except Exception as e:
        await db.rollback()
        print(f"Error creating assistant: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create assistant: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    """Mevcut kullanıcının konuşmalarını listeler."""
    try:
        print(f"Fetching conversations for user: {current_user.id}")
        query = (
            select(Conversation)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        conversations = result.scalars().all()

        response_list = []
        for conv in conversations:
            # Konuşmaya ait mesajları al
            messages_query = select(Message).where(Message.conversation_id == conv.id)
            messages_result = await db.execute(messages_query)
            messages = messages_result.scalars().all()

            # Asistanı bul
            assistant_query = select(AssistantModel).where(AssistantModel.id == conv.assistant_id)
            assistant_result = await db.execute(assistant_query)
            db_assistant = assistant_result.scalar_one_or_none()

            response_list.append(
                ConversationResponse(
                    id=conv.id,
                    name=conv.name,
                    assistant_id=conv.assistant_id,
                    assistant_name=db_assistant.name if db_assistant else "Unknown",
                    session_id=conv.session_id,
                    user_id=conv.user_id,
                    created_at=conv.created_at,
                    messages=[MessageResponse.from_orm(msg) for msg in messages]
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
    """Belirli bir konuşmadaki tüm mesajları döndürür."""
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
    """Belirli bir konuşmayı siler (mesajlarıyla birlikte)."""
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


@router.get("/models", response_model=Dict[str, List[str]])
async def list_models(current_user: User = Depends(get_current_user)):
    """OpenAI ve Ollama modellerini listeler."""
    try:
        openai_service = OpenAIService()
        ollama_service = OllamaService()

        openai_models = await openai_service.list_models()
        ollama_models = await ollama_service.list_models()

        return {
            "openai": openai_models,
            "ollama": ollama_models
        }

    except Exception as e:
        print(f"Error in list_models: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch models: {str(e)}"
        )
