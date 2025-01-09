from fastapi import APIRouter, HTTPException, Depends
from typing import List, AsyncGenerator, Optional
from sqlalchemy import select
from api.schemas import AssistantCreate, AssistantResponse
from api.dependencies import assistants
from core.services.openai_service import OpenAIService
from core.services.ollama_service import OllamaService
from core.models.assistant import Assistant as AssistantClass
from core.database.session import get_db
from core.database.models import Assistant as AssistantModel, Conversation, Message
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
import os
import json
import uuid
from datetime import datetime

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
            print(f"Processing assistant: {assistant.name}")
            response_list.append(
                AssistantResponse(
                    name=assistant.name,
                    model_type=assistant.model_type,
                    system_message=assistant.system_message,
                    has_rag=False  # Şimdilik False olarak bırakalım
                )
            )
        
        return response_list
        
    except Exception as e:
        print(f"Error in list_assistants: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{name}/chat/stream")
async def chat_stream(
    name: str,
    message: str,
    conversation_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(AssistantModel).where(AssistantModel.name == name)
        result = await db.execute(query)
        db_assistant = result.scalar_one_or_none()
        
        if not db_assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")

        if not conversation_id:
            new_conversation = Conversation(
                assistant_id=db_assistant.id
            )
            db.add(new_conversation)
            await db.commit()
            await db.refresh(new_conversation)
            conversation_id = new_conversation.id

        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=message
        )
        db.add(user_message)
        await db.commit()

        if name not in assistants:
            if db_assistant.model_type == "openai":
                model = OpenAIService(api_key=os.getenv("OPENAI_API_KEY"))
            elif db_assistant.model_type == "ollama":
                model = OllamaService()
            else:
                raise HTTPException(status_code=400, detail="Invalid model type")
            
            assistant = AssistantClass(
                name=db_assistant.name,
                model=model,
                system_message=db_assistant.system_message,
                config=json.loads(db_assistant.config) if db_assistant.config else {}
            )
            assistants[name] = assistant

        async def generate() -> AsyncGenerator[str, None]:
            full_response = ""
            try:
                async for chunk in assistants[name].process_message(message, stream=True):
                    if chunk:
                        full_response += chunk
                        yield f"data: {chunk}\n\n"
                
                assistant_message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response
                )
                db.add(assistant_message)
                await db.commit()
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                print(f"Stream generation error: {str(e)}")
                yield f"data: error: {str(e)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Conversation-Id": str(conversation_id)
            }
        )

    except Exception as e:
        print(f"Chat stream error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 

@router.post("/create", response_model=AssistantResponse)
async def create_assistant(
    assistant: AssistantCreate,
    db: AsyncSession = Depends(get_db)
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
            id=str(uuid.uuid4()),  # Unique ID oluştur
            name=assistant.name,
            model_type=assistant.model_type,
            system_message=assistant.system_message,
            config=assistant.config,
            created_at=current_time,
            updated_at=current_time
        )
        
        db.add(db_assistant)
        await db.commit()
        await db.refresh(db_assistant)
        
        print(f"Assistant created successfully: {db_assistant.name}")
        
        return AssistantResponse(
            name=db_assistant.name,
            model_type=db_assistant.model_type,
            system_message=db_assistant.system_message,
            has_rag=False
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in create_assistant: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 