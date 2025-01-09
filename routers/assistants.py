from fastapi import APIRouter, HTTPException, Depends
from typing import List, AsyncGenerator
from sqlalchemy import select
from api.schemas import AssistantCreate, AssistantResponse
from api.dependencies import assistants
from core.services.openai_service import OpenAIService
from core.services.ollama_service import OllamaService
from core.models.assistant import Assistant as AssistantClass
from core.database.session import get_db
from core.database.models import Assistant as AssistantModel
from sqlalchemy.ext.asyncio import AsyncSession
import os
from fastapi.responses import StreamingResponse
import json
import asyncio

router = APIRouter(
    prefix="/assistants",
    tags=["assistants"]
)

@router.post("/create", response_model=AssistantResponse)
async def create_assistant(
    assistant_data: AssistantCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Önce DB'de aynı isimde asistan var mı kontrol et
        query = select(AssistantModel).where(AssistantModel.name == assistant_data.name)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=400, detail="Assistant already exists")
        
        # Model seçimi
        if assistant_data.model_type == "openai":
            model = OpenAIService(api_key=os.getenv("OPENAI_API_KEY"))
        elif assistant_data.model_type == "ollama":
            model = OllamaService()
        else:
            raise HTTPException(status_code=400, detail="Invalid model type")
        
        # Memory'de asistanı oluştur
        assistant = AssistantClass(
            name=assistant_data.name,
            model=model,
            system_message=assistant_data.system_message,
            config=assistant_data.config
        )
        
        # Memory'de sakla
        assistants[assistant_data.name] = assistant
        
        # DB'ye kaydet
        db_assistant = AssistantModel(
            name=assistant_data.name,
            model_type=assistant_data.model_type,
            system_message=assistant_data.system_message,
            config=assistant_data.config
        )
        db.add(db_assistant)
        await db.commit()
        
        return AssistantResponse(
            name=assistant_data.name,
            model_type=assistant_data.model_type,
            system_message=assistant_data.system_message,
            has_rag=bool(assistant.rag_systems)
        )
        
    except Exception as e:
        print(f"Error creating assistant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=List[AssistantResponse])
async def list_assistants(db: AsyncSession = Depends(get_db)):
    try:
        # DB'den tüm asistanları çek
        query = select(AssistantModel)
        result = await db.execute(query)
        db_assistants = result.scalars().all()
        
        print("Found assistants:", [str(a) for a in db_assistants])  # Debug için
        
        # Response listesini oluştur
        response_list = []
        for db_assistant in db_assistants:
            # Memory'de olmayan asistanları yükle
            if db_assistant.name not in assistants:
                # Model seçimi
                if db_assistant.model_type == "openai":
                    model = OpenAIService(api_key=os.getenv("OPENAI_API_KEY"))
                elif db_assistant.model_type == "ollama":
                    model = OllamaService()
                else:
                    continue  # Geçersiz model tipini atla
                
                # Asistanı oluştur ve memory'e yükle
                assistant = AssistantClass(
                    name=db_assistant.name,
                    model=model,
                    system_message=db_assistant.system_message,
                    config=db_assistant.config
                )
                assistants[db_assistant.name] = assistant
            
            # Response'a ekle
            response_list.append(AssistantResponse(
                name=db_assistant.name,
                model_type=db_assistant.model_type,
                system_message=db_assistant.system_message,
                has_rag=bool(assistants.get(db_assistant.name, {}).rag_systems)
            ))
        
        return response_list
        
    except Exception as e:
        print(f"Error listing assistants: {str(e)}")
        await db.rollback()  # Hata durumunda rollback yap
        raise HTTPException(status_code=500, detail=str(e)) 

@router.get("/{name}/chat/stream")
async def chat_stream(
    name: str,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Asistanı bul
        query = select(AssistantModel).where(AssistantModel.name == name)
        result = await db.execute(query)
        db_assistant = result.scalar_one_or_none()
        
        if not db_assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
            
        # Memory'de asistan var mı kontrol et
        if name not in assistants:
            # Model seçimi
            if db_assistant.model_type == "openai":
                model = OpenAIService(api_key=os.getenv("OPENAI_API_KEY"))
            elif db_assistant.model_type == "ollama":
                model = OllamaService()
            else:
                raise HTTPException(status_code=400, detail="Invalid model type")
            
            # Asistanı oluştur
            assistant = AssistantClass(
                name=db_assistant.name,
                model=model,
                system_message=db_assistant.system_message,
                config=db_assistant.config
            )
            assistants[name] = assistant

        async def generate() -> AsyncGenerator[str, None]:
            try:
                async for chunk in assistants[name].process_message(message, stream=True):
                    if chunk:
                        # SSE formatında yanıt gönder
                        yield f"data: {chunk}\n\n"
                # Stream'in sonunu belirt
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
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        print(f"Chat stream error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 