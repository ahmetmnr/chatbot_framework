# Path: chatbot_framework/core/services/openai_service.py

from .base_model import BaseLanguageModel
from openai import AsyncOpenAI
from typing import List, Optional, AsyncGenerator, Union, Dict

class OpenAIService(BaseLanguageModel):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", timeout: int = 30):
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model

    async def generate(
        self, 
        prompt: str, 
        messages: List[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        try:
            if messages:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=False,
                    **kwargs
                )
            else:
                messages = []
                if self.system_message:
                    messages.append({"role": "system", "content": self.system_message})
                messages.append({"role": "user", "content": prompt})
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=False,
                    **kwargs
                )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI Generate Error: {str(e)}")
            raise

    async def stream_generate(
        self,
        prompt: str,
        messages: List[Dict[str, str]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        try:
            if messages:
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    **kwargs
                )
            else:
                messages = []
                if self.system_message:
                    messages.append({"role": "system", "content": self.system_message})
                messages.append({"role": "user", "content": prompt})
                
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
            print(f"OpenAI Stream Error: {str(e)}")
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
