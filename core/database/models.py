from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from .session import Base
from datetime import datetime
import uuid

class Assistant(Base):
    __tablename__ = "assistants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    model_type = Column(String)  # "openai" veya "ollama"
    system_message = Column(String, nullable=True)
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="assistant")
    rag_systems = relationship("RAGSystem", back_populates="assistant")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    assistant_id = Column(String, ForeignKey("assistants.id"))
    session_id = Column(String, index=True)
    user_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assistant = relationship("Assistant", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)  # "user" veya "assistant"
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")
    rag_results = relationship("RAGResult", back_populates="message")

class RAGSystem(Base):
    __tablename__ = "rag_systems"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    assistant_id = Column(String, ForeignKey("assistants.id"))
    name = Column(String)
    weight = Column(Float, default=1.0)
    enabled = Column(Boolean, default=True)
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assistant = relationship("Assistant", back_populates="rag_systems")

class RAGResult(Base):
    __tablename__ = "rag_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"))
    rag_system_id = Column(String, ForeignKey("rag_systems.id"))
    context = Column(String)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    message = relationship("Message", back_populates="rag_results") 