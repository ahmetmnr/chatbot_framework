# Path: chatbot_framework/core/services/openai_service.py

from typing import AsyncIterator, Optional
from openai import AsyncOpenAI
import os

class OpenAIService:
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"

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
