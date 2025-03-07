from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from .models import Assistant as DBAssistant, Assistant  # Add Assistant here
from .models import Conversation, Message, RAGDocument
from datetime import datetime
import hashlib
from core.schemas.enums import ProcessingStatus, FileType  # Add this import

class AssistantDB:
    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        model_type: str,
        model_name: str,
        system_message: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> DBAssistant:
        db_assistant = DBAssistant(
            name=name,
            model_type=model_type,
            model_name=model_name,
            system_message=system_message,
            config=config
        )
        db.add(db_assistant)
        await db.commit()
        await db.refresh(db_assistant)
        return db_assistant

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[DBAssistant]:
        result = await db.execute(
            select(DBAssistant).where(DBAssistant.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession) -> List[DBAssistant]:
        result = await db.execute(select(DBAssistant))
        return result.scalars().all()

class ConversationDB:
    @staticmethod
    async def create(
        db: AsyncSession,
        assistant_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Conversation:
        conversation = Conversation(
            assistant_id=assistant_id,
            session_id=session_id,
            user_id=user_id
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        #rag_results: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        await db.commit()
        
        #if rag_results:
            # RAGResult tablosu mevcut değil, bu kısmı kaldırıyoruz
            # for result in rag_results:
            #     rag_result = RAGResult(
            #         message_id=message.id,
            #         rag_system_id=result["system_id"],
            #         context=result["context"],
            #         metadata=result.get("metadata")
            #     )
            #     db.add(rag_result)
            #await db.commit()
        
        return message

    @staticmethod
    async def get_conversation_history(
        db: AsyncSession,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(Message)
            .join(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(Message.created_at)
            .limit(limit)
        )
        messages = result.scalars().all()
        
        history = []
        for msg in messages:
            rag_data = []
            for rag_result in msg.rag_results:
                rag_data.append({
                    "system_id": rag_result.rag_system_id,
                    "context": rag_result.context,
                    "metadata": rag_result.metadata
                })
            
            history.append({
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
                "rag_results": rag_data
            })
        
        return history 

async def create_rag_document(db: AsyncSession, document_data: dict):
    """Var olan metodun güncellenmiş hali"""
    # Zorunlu alanlar için default değerler
    default_values = {
        "content": "",
        "processing_status": ProcessingStatus.pending,
        "file_type": FileType.unknown,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "file_checksum": hashlib.sha256().hexdigest()[:64],  # Boş dosya için default checksum
        "chunk_size": 1000  # Default chunk size
    }
    
    # Mevcut veriyle default'ları birleştir
    final_data = {**default_values, **document_data}
    
    # Veritabanı constraint'lerine uygun hale getir
    rag_doc = RAGDocument(**final_data)
    
    db.add(rag_doc)
    await db.commit()
    await db.refresh(rag_doc)
    return rag_doc

async def create_assistant(db: AsyncSession, assistant_data: dict):
    """Yeni eklenen metod"""
    assistant = Assistant(
        name=assistant_data["name"],
        model_type=assistant_data["model_type"],
        system_message=assistant_data.get("system_message", ""),
        config=assistant_data.get("config", {}),
        creator_id=assistant_data["creator_id"],
        model_name=assistant_data.get("model_name", "gpt-3.5-turbo"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(assistant)
    await db.commit()
    await db.refresh(assistant)
    return assistant

async def update_rag_document_partial(db: AsyncSession, doc_id: str, updates: dict):
    """Var olan update metodunu bozmayan yeni versiyon"""
    doc = await db.get(RAGDocument, doc_id)
    if not doc:
        return None
    
    for key, value in updates.items():
        if hasattr(doc, key):
            setattr(doc, key, value)
    
    doc.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(doc)
    return doc 