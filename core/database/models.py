from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .db_connection import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assistants = relationship("Assistant", back_populates="creator")
    conversations = relationship("Conversation", back_populates="user")
    rag_documents = relationship("RAGDocument", back_populates="user")
    rag_collections = relationship("RAGCollection", back_populates="user")

class Assistant(Base):
    __tablename__ = "assistants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True)
    model_type = Column(String)
    model_name = Column(String)
    system_message = Column(String)
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    creator_id = Column(String, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", back_populates="assistants")
    conversations = relationship("Conversation", back_populates="assistant")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id"))
    session_id = Column(String)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime)
    
    # Relationships
    assistant = relationship("Assistant", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")

class RAGDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="rag_documents")
    collections = relationship(
        "RAGCollection",
        secondary="rag_document_collections",
        back_populates="documents"
    )

class RAGCollection(Base):
    __tablename__ = "rag_collections"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="rag_collections")
    documents = relationship(
        "RAGDocument",
        secondary="rag_document_collections",
        back_populates="collections"
    )

class RAGDocumentCollection(Base):
    __tablename__ = "rag_document_collections"

    document_id = Column(String, ForeignKey("rag_documents.id"), primary_key=True)
    collection_id = Column(String, ForeignKey("rag_collections.id"), primary_key=True) 