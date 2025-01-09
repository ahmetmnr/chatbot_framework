from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from typing import List, Optional, Dict, Any
import asyncio
import os

from api.schemas import (
    AssistantCreate,
    AssistantResponse,
    ChatMessage,
    ChatResponse
)
from api.dependencies import get_assistant, assistants
from core.services.openai_service import OpenAIService
from core.services.ollama_service import OllamaService
from core.models.assistant import Assistant

router = APIRouter(
    prefix="/assistants",
    tags=["assistants"]
)

@router.post("/create", response_model=AssistantResponse)
async def create_assistant(assistant_data: AssistantCreate):
    print(f"Received create request: {assistant_data}")  # Debug için
    if assistant_data.name in assistants:
        raise HTTPException(status_code=400, detail="Assistant already exists")
    
    try:
        if assistant_data.model_type == "openai":
            model = OpenAIService(api_key=os.getenv("OPENAI_API_KEY"))
        elif assistant_data.model_type == "ollama":
            model = OllamaService()
        else:
            raise HTTPException(status_code=400, detail="Invalid model type")
        
        assistants[assistant_data.name] = Assistant(
            name=assistant_data.name,
            model=model,
            system_message=assistant_data.system_message,
            config=assistant_data.config
        )
        
        return AssistantResponse(
            name=assistant_data.name,
            model_type=assistant_data.model_type,
            system_message=assistant_data.system_message,
            has_rag=bool(assistants[assistant_data.name].rag_systems)
        )
    except Exception as e:
        print(f"Error creating assistant: {str(e)}")  # Debug için
        raise HTTPException(status_code=500, detail=f"Error creating assistant: {str(e)}")

@router.post("/{name}/chat", response_model=ChatResponse)
async def chat_with_assistant(
    name: str,
    chat: ChatMessage,
    assistant: Assistant = Depends(get_assistant)
):
    response = await assistant.process_message(chat.message)
    return ChatResponse(response=response)

@router.get("/{name}/chat/stream")
async def chat_with_assistant_stream(
    request: Request,
    name: str,
    message: str,
    assistant: Assistant = Depends(get_assistant)
):
    async def event_generator():
        try:
            response_generator = await assistant.process_message(message, stream=True)
            async for token in response_generator:
                if await request.is_disconnected():
                    break
                yield {"data": token}
                await asyncio.sleep(0.01)
        except Exception as e:
            yield {"data": f"Error: {str(e)}"}
            
    return EventSourceResponse(event_generator())

@router.get("/list", response_model=List[AssistantResponse])
async def list_assistants():
    return [
        AssistantResponse(
            name=name,
            model_type=type(assistant.model).__name__,
            system_message=assistant.system_message,
            has_rag=bool(assistant.rag_systems)
        )
        for name, assistant in assistants.items()
    ] 