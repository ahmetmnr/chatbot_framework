from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from pgvector.asyncpg import register_vector
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from config.settings import settings

class BaseVectorStore(ABC):
    """Vector store için temel sınıf"""
    
    @abstractmethod
    async def add_embeddings(self, texts: List[str], embeddings: List[List[float]], metadata: Optional[List[Dict]] = None):
        """Embedding'leri vector store'a ekle"""
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """En yakın k dökümanı bul"""
        pass

class PGVectorStore(BaseVectorStore):
    """PostgreSQL pgvector extension kullanan vector store"""
    
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)
        
    async def init_db(self):
        """pgvector extension'ı yükle ve tabloyu oluştur"""
        async with self.engine.begin() as conn:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS document_embeddings (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding vector(1536) NOT NULL,
                    metadata JSONB
                )
            ''')
            await register_vector(conn)
    
    async def add_embeddings(self, texts: List[str], embeddings: List[List[float]], metadata: Optional[List[Dict]] = None):
        if metadata is None:
            metadata = [{}] * len(texts)
            
        async with self.engine.begin() as conn:
            for text, embedding, meta in zip(texts, embeddings, metadata):
                await conn.execute(
                    '''
                    INSERT INTO document_embeddings (text, embedding, metadata)
                    VALUES ($1, $2, $3)
                    ''',
                    text, embedding, meta
                )
    
    async def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            results = await conn.fetch(
                '''
                SELECT text, embedding <-> $1 as distance, metadata
                FROM document_embeddings
                ORDER BY distance ASC
                LIMIT $2
                ''',
                query_embedding, k
            )
            
            return [
                {
                    'text': row['text'],
                    'distance': float(row['distance']),
                    'metadata': row['metadata']
                }
                for row in results
            ]

# Factory pattern for vector store creation
def get_vector_store() -> BaseVectorStore:
    if settings.VECTOR_STORE_TYPE == "pgvector":
        return PGVectorStore()
    else:
        raise ValueError(f"Unsupported vector store type: {settings.VECTOR_STORE_TYPE}") 