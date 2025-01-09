# Path: chatbot_framework/test_core.py
import asyncio
import os
from dotenv import load_dotenv
from core.services.openai_service import OpenAIService
from core.services.ollama_service import OllamaService
from core.models.assistant import Assistant

async def test_assistants():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in .env file")
    
    # OpenAI asistanını test et
    print("\n=== Testing OpenAI Assistant ===")
    try:
        openai_service = OpenAIService(api_key=api_key)
        openai_assistant = Assistant(
            name="OpenAI Assistant",
            model=openai_service,
            system_message="You are a helpful assistant."
        )
        
        # Normal yanıt testi
        print("\nTesting normal response:")
        response = await openai_assistant.process_message("merhaba nasılsın")
        print(f"OpenAI Response: {response}")
        
        # Streaming yanıt testi
        print("\nTesting streaming response:")
        print("OpenAI Streaming Response: ", end="", flush=True)
        async for token in await openai_assistant.process_message(
            "merhaba nasılsın", 
            stream=True
        ):
            print(token, end="", flush=True)
        print()  # Yeni satır
        
    except Exception as e:
        print(f"OpenAI Test Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

    # Ollama asistanını test et
    print("\n=== Testing Ollama Assistant ===")
    try:
        ollama_service = OllamaService(model="llama3.2")
        ollama_assistant = Assistant(
            name="Ollama Assistant",
            model=ollama_service,
            system_message="You are a helpful assistant."
        )
        
        # Normal yanıt testi
        print("\nTesting normal response:")
        response = await ollama_assistant.process_message("merhaba nasılsıns")
        print(f"Ollama Response: {response}")
        
        # Streaming yanıt testi
        print("\nTesting streaming response:")
        print("Ollama Streaming Response: ", end="", flush=True)
        async for token in await ollama_assistant.process_message(
            "merhaba nasılsın", 
            stream=True
        ):
            print(token, end="", flush=True)
        print()  # Yeni satır
        
    except Exception as e:
        print(f"Ollama Test Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_assistants()) 