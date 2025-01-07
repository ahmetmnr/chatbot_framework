# Path: chatbot_framework/scripts/test_database.py
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random

# Proje kök dizinini Python path'ine ekle
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from core.database.session import async_session
from core.database.models import Assistant, Conversation, Message, RAGSystem, RAGResult

async def test_database():
    try:
        async with async_session() as session:
            # 1. Asistan oluştur
            print("\n=== Creating Assistant ===")
            assistant_name = f"Test Assistant {random.randint(1000,9999)}"
            assistant = Assistant(
                name=assistant_name,
                model_type="openai",
                system_message="You are a helpful assistant.",
                config={"temperature": 0.7}
            )
            session.add(assistant)
            await session.commit()
            print(f"Assistant created with ID: {assistant.id}")

            # 2. RAG sistemi ekle
            print("\n=== Adding RAG System ===")
            rag_system = RAGSystem(
                assistant_id=assistant.id,
                name="Test RAG",
                weight=1.0,
                enabled=True,
                config={"source": "test_documents"}
            )
            session.add(rag_system)
            await session.commit()
            print(f"RAG System created with ID: {rag_system.id}")

            # 3. Konuşma başlat
            print("\n=== Starting Conversation ===")
            conversation = Conversation(
                assistant_id=assistant.id,
                session_id="test_session",
                user_id="test_user"
            )
            session.add(conversation)
            await session.commit()
            print(f"Conversation created with ID: {conversation.id}")

            # 4. Mesajlar ekle
            print("\n=== Adding Messages ===")
            # Kullanıcı mesajı
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content="What is the meaning of life?"
            )
            session.add(user_message)
            await session.commit()
            print(f"User message created with ID: {user_message.id}")

            # Asistan mesajı
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content="The meaning of life is 42."
            )
            session.add(assistant_message)
            await session.commit()
            print(f"Assistant message created with ID: {assistant_message.id}")

            # 5. RAG sonucu ekle
            print("\n=== Adding RAG Result ===")
            rag_result = RAGResult(
                message_id=assistant_message.id,
                rag_system_id=rag_system.id,
                context="Found in Hitchhiker's Guide to the Galaxy",
                meta_data={"confidence": 0.95}
            )
            session.add(rag_result)
            await session.commit()
            print(f"RAG Result created with ID: {rag_result.id}")

            # 6. Verileri kontrol et
            print("\n=== Checking Data ===")
            # Tüm ilişkili verileri tek seferde çek
            stmt = select(Assistant).where(Assistant.id == assistant.id).options(
                selectinload(Assistant.conversations).selectinload(Conversation.messages).selectinload(Message.rag_results)
            )
            result = await session.execute(stmt)
            db_assistant = result.scalar_one()

            print(f"\nAssistant: {db_assistant.name}")
            print(f"Model Type: {db_assistant.model_type}")
            print(f"System Message: {db_assistant.system_message}")
            
            # İlişkili verileri göster
            for conv in db_assistant.conversations:
                print(f"\nConversation ID: {conv.id}")
                print(f"Session ID: {conv.session_id}")
                print("\nMessages:")
                for msg in conv.messages:
                    print(f"- {msg.role}: {msg.content}")
                    if msg.rag_results:
                        for rag in msg.rag_results:
                            print(f"  RAG Context: {rag.context}")
                            print(f"  RAG Meta Data: {rag.meta_data}")

    except Exception as e:
        print(f"Error during database test: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    asyncio.run(test_database()) 