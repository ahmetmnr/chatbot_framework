from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    hashed_password: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class AssistantCreate(BaseModel):
    name: str
    model_type: str  # "openai" veya "ollama"
    model_name: str  # "gpt-4", "llama2" gibi
    system_message: str
    config: dict = {}

class AssistantResponse(BaseModel):
    id: str
    name: str
    model_type: str
    system_message: str
    config: Optional[Dict] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_id: Optional[str] = None

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
    name: str
    assistant_id: str
    assistant_name: str
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