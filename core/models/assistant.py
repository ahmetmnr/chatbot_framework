# Path: chatbot_framework/core/models/assistant.py

from typing import Union, AsyncGenerator, Optional, Dict, List, Any
from ..services.base_model import BaseLanguageModel

class Assistant:
    def __init__(
        self,
        name: str,
        model: BaseLanguageModel,
        system_message: Optional[str] = None,
        max_history: int = 10,
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.model = model
        self.system_message = system_message
        self.max_history = max_history
        self.conversation_history = []  # [{"role": "user/assistant", "content": "..."}]
        self.rag_systems = {}
        self.config = config or {}

    async def process_message(
        self, 
        message: str, 
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        try:
            # Yeni mesajı geçmişe ekle
            self.conversation_history.append({
                "role": "user",
                "content": message
            })

            # Mesaj listesini hazırla
            messages = []
            
            # Sistem mesajını ekle
            if self.system_message:
                messages.append({"role": "system", "content": self.system_message})
            
            # Son N mesajı ekle
            start_idx = max(0, len(self.conversation_history) - self.max_history)
            messages.extend(self.conversation_history[start_idx:])

            # RAG işleme
            if self.rag_systems:
                rag_results = await self._query_rag_systems(message)
                if rag_results["combined_context"]:
                    # RAG sonuçlarını sistem mesajı olarak ekle
                    messages.append({
                        "role": "system",
                        "content": f"""
Information from knowledge bases:
{rag_results['combined_context']}

Please use the above information to answer the question.
"""
                    })

            if not stream:
                # Normal yanıt
                response = await self.model.generate(
                    prompt=message,  # Geriye uyumluluk için
                    messages=messages,  # Tüm geçmişi gönder
                    **kwargs
                )
                # Asistan yanıtını geçmişe ekle
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                return response

            # Stream yanıt için generator fonksiyon
            async def stream_response():
                response_text = ""
                async for token in self.model.stream_generate(
                    prompt=message,  # Geriye uyumluluk için
                    messages=messages,  # Tüm geçmişi gönder
                    **kwargs
                ):
                    response_text += token
                    yield token
                
                # Stream bittikten sonra yanıtı geçmişe ekle
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_text
                })

            return stream_response()

        except Exception as e:
            print(f"Assistant Process Error: {str(e)}")
            raise