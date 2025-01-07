import asyncio
import asyncpg
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

async def recreate_tables():
    load_dotenv()
    
    # Database credentials
    DB_NAME = os.getenv("DB_NAME", "chatbot")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "**Malatya44")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    
    try:
        # Database'e bağlan
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        # Tüm tabloları sil
        await conn.execute("""
            DROP TABLE IF EXISTS 
                rag_results, 
                messages, 
                conversations, 
                rag_systems, 
                assistants 
            CASCADE
        """)
        
        await conn.close()
        print("Existing tables dropped successfully!")
        
        # Tabloları yeniden oluştur
        from core.database.session import init_db
        await init_db()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(recreate_tables()) 