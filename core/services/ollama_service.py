# Path: chatbot_framework/core/services/ollama_service.py

from .base_model import BaseLanguageModel
import httpx
from typing import List, Optional, AsyncGenerator, Union, AsyncIterator
import json

class OllamaService(BaseLanguageModel):
    def __init__(self, 
                 base_url: str = "http://localhost:11434", 
                 model: str = "llama3.2",
                 timeout: int = 30):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(self, 
                      prompt: str, 
                      system_message: Optional[str] = None,
                      **kwargs) -> str:
        try:
            if system_message:
                prompt = f"{system_message}\n\n{prompt}"
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.text}")
                
            return response.json()["response"]

        except Exception as e:
            print(f"Ollama Generate Error: {str(e)}")
            raise

    async def stream_generate(self,
                            prompt: str,
                            system_message: Optional[str] = None,
                            **kwargs) -> AsyncGenerator[str, None]:
        try:
            if system_message:
                prompt = f"{system_message}\n\n{prompt}"
                
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    **kwargs
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                            
        except Exception as e:
            print(f"Ollama Streaming Error: {str(e)}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            for text in texts:
                response = await self.client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API error: {response.text}")
                    
                response_data = response.json()
                embeddings.append(response_data.get("embedding", []))
            return embeddings
        except Exception as e:
            print(f"Ollama Embeddings Error: {str(e)}")
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def chat_stream(self, message: str, system_message: Optional[str] = None) -> AsyncIterator[str]:
        try:
            prompt = message
            if system_message:
                prompt = f"{system_message}\n\nUser: {message}\nAssistant:"

            async with httpx.AsyncClient() as client:
                async with client.stream(
                    'POST',
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            print(f"Ollama stream error: {str(e)}")
            yield f"Error: {str(e)}"

    async def chat(self, message: str, system_message: Optional[str] = None) -> str:
        try:
            prompt = message
            if system_message:
                prompt = f"{system_message}\n\nUser: {message}\nAssistant:"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt
                    }
                )
                data = response.json()
                return data.get("response", "")

        except Exception as e:
            print(f"Ollama chat error: {str(e)}")
            return f"Error: {str(e)}"

    async def list_models(self) -> List[str]:
        """Ollama modellerini listeler."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f'{self.base_url}/v1/models')
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "data" in data:
                        return sorted([
                            model["id"].split(':')[0]
                            for model in data["data"]
                        ])
        except Exception as e:
            print(f"Ollama API error: {str(e)}")
            return []
        return []
