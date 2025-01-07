# Path: chatbot_framework/core/services/base_model.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator, Union

class BaseLanguageModel(ABC):
    """Tüm dil modelleri için temel arayüz"""
    
    @abstractmethod
    async def generate(self, 
                      prompt: str, 
                      system_message: Optional[str] = None,
                      stream: bool = False,
                      **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """Metin üretimi için temel metod
        
        Args:
            prompt: Kullanıcı mesajı
            system_message: Sistem talimatları
            stream: True ise token token streaming yanıt döner
            **kwargs: Ek model parametreleri
            
        Returns:
            stream=True ise: AsyncGenerator[str, None] - Token token yanıtlar
            stream=False ise: str - Tam yanıt
        """
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Metin embedding'leri için temel metod"""
        pass 