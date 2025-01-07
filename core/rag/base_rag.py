# Path: chatbot_framework/core/rag/base_rag.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseRAG(ABC):
    """RAG sistemleri için temel sınıf"""
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Dökümanları indexe ekle"""
        pass

    @abstractmethod
    async def query(self, question: str) -> Dict[str, Any]:
        """Soru sorma ve ilgili dökümanları getirme"""
        pass

    @abstractmethod
    async def update_index(self) -> None:
        """Index'i güncelle"""
        pass 