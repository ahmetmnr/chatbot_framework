# Path: chatbot_framework/core/models/assistant.py

from typing import AsyncIterator, Optional, Dict, Any
import json

class Assistant:
    def __init__(self, name: str, model, system_message: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.model = model
        self.system_message = system_message
        self.config = config or {}
        self.rag_systems = []

    async def process_message(self, message: str, stream: bool = False) -> AsyncIterator[str]:
        try:
            if stream:
                async for chunk in self.model.chat_stream(message, self.system_message):
                    yield chunk
            else:
                response = await self.model.chat(message, self.system_message)
                yield response
                
        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            yield f"Error: {str(e)}"