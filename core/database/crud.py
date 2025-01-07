from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from .models import Assistant as DBAssistant
from .models import Conversation, Message, RAGSystem, RAGResult
from datetime import datetime

class AssistantDB:
    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        model_type: str,
        system_message: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> DBAssistant:
        db_assistant = DBAssistant(
            name=name,
            model_type=model_type,
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
        rag_results: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        await db.commit()
        
        if rag_results:
            for result in rag_results:
                rag_result = RAGResult(
                    message_id=message.id,
                    rag_system_id=result["system_id"],
                    context=result["context"],
                    metadata=result.get("metadata")
                )
                db.add(rag_result)
            await db.commit()
        
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