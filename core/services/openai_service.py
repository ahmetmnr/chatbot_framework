# Path: chatbot_framework/core/services/openai_service.py

from .base_model import BaseLanguageModel
from openai import AsyncOpenAI
from typing import List, Optional, AsyncGenerator, Union, Dict

class OpenAIService(BaseLanguageModel):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        
    async def generate(self, 
                      prompt: str, 
                      system_message: Optional[str] = None,
                      stream: bool = False,
                      **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            if stream:
                return self._stream_response(messages, **kwargs)
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=False,
                    **kwargs
                )
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            raise

    async def _stream_response(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Token token yanıt üretir"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"OpenAI Streaming Error: {str(e)}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            for text in texts:
                response = await self.client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                embeddings.append(response.data[0].embedding)
            return embeddings
        except Exception as e:
            print(f"OpenAI Embeddings Error: {str(e)}")
            raise
