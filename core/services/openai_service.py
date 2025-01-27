# Path: chatbot_framework/core/services/openai_service.py

from typing import AsyncIterator, Optional, List
from openai import AsyncOpenAI
import os

class OpenAIService:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    async def list_models(self) -> List[str]:
        """OpenAI modellerini listeler."""
        try:
            response = await self.client.models.list()
            return sorted([
                model.id for model in response.data 
                if any(x in model.id.lower() for x in ["gpt-3.5", "gpt-4"])
            ])
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return []

    async def chat_stream(self, message: str, system_message: Optional[str] = None) -> AsyncIterator[str]:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": message})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            print(f"OpenAI stream error: {str(e)}")
            yield f"Error: {str(e)}"

    async def chat(self, message: str, system_message: Optional[str] = None) -> str:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": message})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI chat error: {str(e)}")
            return f"Error: {str(e)}"
