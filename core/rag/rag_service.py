from typing import List, Dict, Any
from .embedding_service import EmbeddingService
from .vector_store import get_vector_store
from config.settings import settings

class RAGService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = get_vector_store()
        
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Dökümanları işle ve vector store'a ekle
        
        Args:
            documents: Her biri {'text': str, 'metadata': dict} formatında döküman listesi
        """
        texts = [doc['text'] for doc in documents]
        metadata = [doc.get('metadata', {}) for doc in documents]
        
        # Metinleri chunk'lara böl
        all_chunks = []
        all_metadata = []
        
        for text, meta in zip(texts, metadata):
            chunks = self.embedding_service.chunk_text(text)
            all_chunks.extend(chunks)
            # Her chunk için metadata'yı kopyala
            all_metadata.extend([meta] * len(chunks))
        
        # Tüm chunk'lar için embedding'leri al
        embeddings = []
        for chunk in all_chunks:
            embedding = await self.embedding_service.get_embedding(chunk)
            embeddings.append(embedding)
        
        # Vector store'a kaydet
        await self.vector_store.add_embeddings(all_chunks, embeddings, all_metadata)
    
    async def query(self, question: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Soru için en alakalı dökümanları bul
        
        Args:
            question: Sorgu metni
            k: Kaç sonuç döndürüleceği
            
        Returns:
            List[Dict]: Her biri {'text': str, 'distance': float, 'metadata': dict} formatında sonuçlar
        """
        # Soru için embedding al
        query_embedding = await self.embedding_service.get_embedding(question)
        
        # En yakın dökümanları bul
        results = await self.vector_store.search(query_embedding, k=k)
        return results 