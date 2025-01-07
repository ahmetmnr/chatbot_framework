from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

class AssistantCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    name: str
    model_type: str
    system_message: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class AssistantResponse(BaseModel):
    name: str
    model_type: str
    system_message: Optional[str]
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