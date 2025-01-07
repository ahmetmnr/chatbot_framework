import asyncio
import os
from dotenv import load_dotenv
from core.services.openai_service import OpenAIService
from core.services.ollama_service import OllamaService
from core.models.assistant import Assistant
from core.rag.simple_rag import SimpleRAG

async def test_multi_rag():
    # .env dosyasından API anahtarını yükle
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Test için örnek dökümanlar
    company_docs = {
        "mission": "Our company mission is to create innovative AI solutions.",
        "products": "We offer chatbot and RAG solutions.",
        "team": "Our team consists of AI researchers and engineers."
    }
    
    technical_docs = {
        "architecture": "The system uses a microservices architecture.",
        "deployment": "We use Docker and Kubernetes for deployment.",
        "api": "REST API documentation includes authentication details."
    }
    
    knowledge_base = {
        "faq": "Common questions about our services and support.",
        "pricing": "Our services start from $99 per month.",
        "contact": "You can reach us at support@example.com"
    }

    try:
        # RAG sistemlerini oluştur
        company_rag = SimpleRAG("Company Info", company_docs)
        tech_rag = SimpleRAG("Technical Docs", technical_docs)
        kb_rag = SimpleRAG("Knowledge Base", knowledge_base)

        # OpenAI asistanını oluştur
        print("\n=== Creating Multi-RAG Assistant ===")
        assistant = Assistant(
            name="Multi-RAG Assistant",
            model=OpenAIService(api_key=api_key),
            system_message="You are a helpful assistant with access to multiple knowledge bases."
        )

        # RAG sistemlerini ekle
        assistant.add_rag_system(company_rag, "Company", weight=1.0)
        assistant.add_rag_system(tech_rag, "Technical", weight=0.8)
        assistant.add_rag_system(kb_rag, "Knowledge Base", weight=0.6)

        # Test senaryoları
        test_questions = [
            "What is our company's mission?",
            "How do we deploy our services?",
            "What are our pricing options?",
            "Tell me about our team and architecture.",  # Bu soru birden fazla RAG'i tetikleyecek
        ]

        for question in test_questions:
            print(f"\n\n=== Testing Question: {question} ===")
            
            # Normal yanıt testi
            print("\nNormal Response:")
            response = await assistant.process_message(question)
            print(response)
            
            # Streaming yanıt testi
            print("\nStreaming Response:", end=" ", flush=True)
            async for token in await assistant.process_message(question, stream=True):
                print(token, end="", flush=True)
            print()  # Yeni satır

            # RAG sistemini devre dışı bırakma testi
            print("\n=== Testing with disabled RAG ===")
            assistant.disable_rag_system("Technical")
            response = await assistant.process_message(question)
            print(response)
            
            # RAG sistemini tekrar etkinleştir
            assistant.enable_rag_system("Technical")

        # Konuşma geçmişini kontrol et
        print("\n=== Conversation History ===")
        for entry in assistant.conversation_history:
            print(f"\nUser: {entry['user']}")
            print(f"Assistant: {entry['assistant']}")
            if entry.get('rag_results'):
                print("RAG Results:", entry['rag_results'])

    except Exception as e:
        print(f"Test Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_multi_rag()) 