from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class AssistantCreate(BaseModel):
    name: str
    model_type: str
    system_message: str
    config: Dict[str, Any]

class AssistantResponse(BaseModel):
    id: str
    name: str
    model_type: str
    system_message: str
    config: Dict[str, Any]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    creator_id: Optional[str]

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    assistant_id: str
    session_id: str
    user_id: str
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class RAGConfig(BaseModel):
    collection_name: str
    embedding_model: str
    chunk_size: int = 1000
    chunk_overlap: int = 200

class RAGDocumentBase(BaseModel):
    title: str
    content: str
    meta_data: Optional[Dict[str, Any]] = None

class RAGDocumentCreate(RAGDocumentBase):
    pass

class RAGDocumentResponse(RAGDocumentBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RAGCollectionBase(BaseModel):
    name: str
    description: Optional[str] = None

class RAGCollectionCreate(RAGCollectionBase):
    pass

class RAGCollectionResponse(RAGCollectionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 