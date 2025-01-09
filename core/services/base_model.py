# Path: chatbot_framework/core/services/base_model.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator, Union

class BaseLanguageModel(ABC):
    """Tüm dil modelleri için temel arayüz"""
    
    @abstractmethod
    async def generate(self, 
                      prompt: str, 
                      messages: Optional[List[Dict[str, str]]] = None,
                      **kwargs) -> str:
        """Tek seferlik yanıt üretme"""
        pass

    @abstractmethod
    async def stream_generate(self,
                            prompt: str,
                            messages: Optional[List[Dict[str, str]]] = None,
                            **kwargs) -> AsyncGenerator[str, None]:
        """Stream şeklinde yanıt üretme"""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Metin embedding'leri için temel metod"""
        pass 