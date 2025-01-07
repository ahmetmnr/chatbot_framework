import asyncio
import asyncpg
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

async def check_tables():
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
        
        # Mevcut tabloları kontrol et
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        print("\nMevcut tablolar:")
        for table in tables:
            print(f"- {table['table_name']}")
            
            # Her tablonun yapısını göster
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = $1
            """, table['table_name'])
            
            print("  Kolonlar:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else 'NOT NULL'
                print(f"    - {col['column_name']}: {col['data_type']} {nullable}")
            print()
            
        await conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(check_tables()) 