import asyncio
import asyncpg
from dotenv import load_dotenv
import os

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
            database="postgres"
        )
        
        # Veritabanının var olup olmadığını kontrol et
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            DB_NAME
        )
        
        if not exists:
            # Database'i oluştur
            await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"Database '{DB_NAME}' created successfully!")
        else:
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