from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .db_connection import Base

class Assistant(Base):
    __tablename__ = "assistants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    model_type = Column(String)
    system_message = Column(String)
    config = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    conversations = relationship("Conversation", back_populates="assistant")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    assistant_id = Column(String, ForeignKey("assistants.id"))
    session_id = Column(String)
    user_id = Column(String)
    created_at = Column(DateTime)
    
    assistant = relationship("Assistant", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime)
    
    conversation = relationship("Conversation", back_populates="messages")
    rag_results = relationship("RAGResult", back_populates="message")

class RAGResult(Base):
    __tablename__ = "rag_results"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    rag_system_id = Column(Integer)
    context = Column(Text)
    meta_data = Column(Text)  # JSON string olarak saklıyoruz
    created_at = Column(DateTime, default=datetime.utcnow)
    
    message = relationship("Message", back_populates="rag_results") 