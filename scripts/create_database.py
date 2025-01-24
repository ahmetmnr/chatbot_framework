import asyncio
import asyncpg
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

async def create_database():
    load_dotenv()
    
    # Database credentials
    DB_NAME = os.getenv("DB_NAME", "chatbot")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "**Malatya44")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    
    try:
        # Önce default database'e bağlan
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database='postgres'
        )
        
        # Database'i oluştur
        try:
            await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"Database '{DB_NAME}' created successfully!")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print(f"Database '{DB_NAME}' already exists!")
            
        await conn.close()
        
        # Yeni database'e bağlan ve tabloları oluştur
        from core.database.session import init_db
        await init_db()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(create_database()) 