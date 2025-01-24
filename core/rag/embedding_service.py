from typing import List, Optional
import numpy as np
from openai import AsyncOpenAI
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings

class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """
        Embedding servisi için yapılandırıcı.
        
        Args:
            api_key: OpenAI API anahtarı (None ise settings'den alınır)
            model: Kullanılacak embedding modeli (None ise settings'den alınır)
        """
        self.client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        self.model = model or settings.EMBEDDING_MODEL
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Metni belirli uzunlukta parçalara böler.
        
        Args:
            text: Bölünecek metin
            chunk_size: Parça boyutu (None ise settings'den alınır)
            overlap: Parçalar arası örtüşme miktarı (None ise settings'den alınır)
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        i = 0
        while i < len(tokens):
            # Parça boyutu kadar token al
            chunk_tokens = tokens[i:i + chunk_size]
            # Token'ları metne çevir
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            # Örtüşme miktarı kadar geri git
            i += chunk_size - overlap
            
        return chunks

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Metinler için embedding'ler üretir.
        
        Args:
            texts: Embedding'i alınacak metinler listesi
            
        Returns:
            List[List[float]]: Embedding vektörleri listesi
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error in get_embeddings: {str(e)}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """
        Tek bir metin için embedding üretir.
        
        Args:
            text: Embedding'i alınacak metin
            
        Returns:
            List[float]: Embedding vektörü
        """
        embeddings = await self.get_embeddings([text])
        return embeddings[0]

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        İki embedding vektörü arasındaki kosinüs benzerliğini hesaplar.
        
        Args:
            embedding1: İlk embedding vektörü
            embedding2: İkinci embedding vektörü
            
        Returns:
            float: Kosinüs benzerlik skoru (0-1 arası)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity) 