# Path: chatbot_framework/core/models/assistant.py

from typing import Optional, Dict, Any, Union, AsyncGenerator, List
from ..services.base_model import BaseLanguageModel
from ..rag.base_rag import BaseRAG

class Assistant:
    def __init__(
        self,
        name: str,
        model: BaseLanguageModel,
        rag_systems: Optional[List[Dict[str, Any]]] = None,
        system_message: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            name: Asistan adı
            model: Dil modeli
            rag_systems: RAG sistemleri listesi. Her biri şu formatta:
                {
                    "system": BaseRAG instance,
                    "name": "RAG sistem adı",
                    "weight": 1.0,  # Sonuçları birleştirirken kullanılacak ağırlık
                    "enabled": True  # RAG sisteminin aktif/pasif durumu
                }
            system_message: Sistem talimatları
            config: Ek yapılandırma
        """
        self.name = name
        self.model = model
        self.rag_systems = rag_systems or []
        self.system_message = system_message
        self.config = config or {}
        self.conversation_history = []

    def add_rag_system(
        self, 
        rag_system: BaseRAG, 
        name: str, 
        weight: float = 1.0,
        enabled: bool = True
    ) -> None:
        """Yeni bir RAG sistemi ekle"""
        self.rag_systems.append({
            "system": rag_system,
            "name": name,
            "weight": weight,
            "enabled": enabled
        })

    def enable_rag_system(self, name: str) -> None:
        """Belirli bir RAG sistemini etkinleştir"""
        for rag in self.rag_systems:
            if rag["name"] == name:
                rag["enabled"] = True
                break

    def disable_rag_system(self, name: str) -> None:
        """Belirli bir RAG sistemini devre dışı bırak"""
        for rag in self.rag_systems:
            if rag["name"] == name:
                rag["enabled"] = False
                break

    async def _query_rag_systems(self, message: str) -> Dict[str, Any]:
        """Tüm aktif RAG sistemlerinden yanıt al ve birleştir"""
        results = []
        
        for rag in self.rag_systems:
            if not rag["enabled"]:
                continue
                
            try:
                result = await rag["system"].query(message)
                results.append({
                    "name": rag["name"],
                    "weight": rag["weight"],
                    "context": result["context"],
                    "metadata": result.get("metadata", {})
                })
            except Exception as e:
                print(f"Error querying RAG system {rag['name']}: {str(e)}")
                continue

        # Sonuçları birleştir
        combined_context = ""
        for result in results:
            combined_context += f"\n=== From {result['name']} (weight: {result['weight']}) ===\n"
            combined_context += result["context"]

        return {
            "combined_context": combined_context,
            "individual_results": results
        }

    async def process_message(
        self, 
        message: str, 
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Mesajı işle ve yanıt üret
        
        Args:
            message: Kullanıcı mesajı
            stream: True ise streaming yanıt döner
            **kwargs: Ek model parametreleri
        """
        try:
            context = message
            
            # Aktif RAG sistemleri varsa sorgula
            if self.rag_systems:
                rag_results = await self._query_rag_systems(message)
                if rag_results["combined_context"]:
                    context = f"""
Information from knowledge bases:
{rag_results['combined_context']}

User Question: {message}

Please use the above information to answer the question. If the information is not relevant or sufficient, you can use your general knowledge.
"""

            # Modelden yanıt al
            response = await self.model.generate(
                prompt=context,
                system_message=self.system_message,
                stream=stream,
                **kwargs
            )

            if not stream:
                # Normal yanıt için konuşma geçmişini güncelle
                self.conversation_history.append({
                    "user": message,
                    "assistant": response,
                    "rag_results": rag_results if self.rag_systems else None
                })
                return response
            else:
                # Streaming yanıt için generator döndür
                async def response_generator():
                    full_response = ""
                    async for token in response:
                        full_response += token
                        yield token
                    # Stream tamamlandığında konuşma geçmişini güncelle
                    self.conversation_history.append({
                        "user": message,
                        "assistant": full_response,
                        "rag_results": rag_results if self.rag_systems else None
                    })
                return response_generator()
                
        except Exception as e:
            print(f"Assistant Process Error: {str(e)}")
            raise 