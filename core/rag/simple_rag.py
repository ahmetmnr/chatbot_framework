from .base_rag import BaseRAG
from typing import List, Dict, Any
import asyncio

class SimpleRAG(BaseRAG):
    """Test için basit bir RAG implementasyonu"""
    
    def __init__(self, name: str, documents: Dict[str, str]):
        """
        Args:
            name: RAG sistemi adı
            documents: Anahtar-değer çiftleri olarak dökümanlar
        """
        self.name = name
        self.documents = documents

    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Yeni dökümanlar ekle"""
        for doc in documents:
            self.documents[doc["id"]] = doc["content"]

    async def query(self, question: str) -> Dict[str, Any]:
        """Basit keyword matching ile ilgili dökümanları bul"""
        # Simüle edilmiş gecikme
        await asyncio.sleep(0.1)
        
        matching_docs = []
        for doc_id, content in self.documents.items():
            # Basit keyword matching
            if any(word.lower() in content.lower() for word in question.split()):
                matching_docs.append(f"[Doc {doc_id}]: {content}")

        context = "\n".join(matching_docs) if matching_docs else "No relevant documents found."
        
        return {
            "context": context,
            "metadata": {
                "source": self.name,
                "matched_docs": len(matching_docs)
            }
        }

    async def update_index(self) -> None:
        """Bu basit implementasyonda index güncellemeye gerek yok"""
        pass 