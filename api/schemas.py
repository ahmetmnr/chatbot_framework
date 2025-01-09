from pydantic import BaseModel
from typing import Dict, Any, Optional

class AssistantCreate(BaseModel):
    name: str
    model_type: str
    system_message: str
    config: Dict[str, Any]

class AssistantResponse(BaseModel):
    name: str
    model_type: str
    system_message: str
    has_rag: bool

class ChatMessage(BaseModel):
    message: str
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str

class RAGConfig(BaseModel):
    name: str
    weight: float = 1.0
    enabled: bool = True 