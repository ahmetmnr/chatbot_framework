# Path: chatbot_framework/test_api.py
import asyncio
import httpx
import json
import aiohttp

async def test_api():
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            # Asistan oluştur
            print("\n=== Creating OpenAI Assistant ===")
            create_data = {
                "name": "test_assistant",
                "model_type": "openai",
                "system_message": "You are a helpful assistant."
            }
            response = await client.post("/assistants/create", json=create_data)
            print(f"Create Response Status: {response.status_code}")
            print(f"Create Response: {response.json()}")

            # Asistanları listele
            print("\n=== Listing Assistants ===")
            response = await client.get("/assistants/list")
            print(f"List Response: {response.json()}")

            # Normal chat testi
            print("\n=== Testing Normal Chat ===")
            chat_data = {
                "message": "What is 2+2?",
                "stream": False
            }
            response = await client.post(
                "/assistants/test_assistant/chat",
                json=chat_data
            )
            print(f"Chat Response: {response.json()}")

            # Streaming chat testi
            print("\n=== Testing Streaming Chat ===")
            print("Streaming Response: ", end="", flush=True)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/assistants/test_assistant/chat/stream",
                    params={"message": "Explain why the sky is blue in 3 sentences."}
                ) as response:
                    async for line in response.content:
                        if line:
                            try:
                                line = line.decode('utf-8').strip()
                                print(f"\nReceived line: {line}")
                                if line.startswith('data: '):
                                    data = line[6:]
                                    print(data, end="", flush=True)
                            except Exception as e:
                                print(f"\nError parsing SSE: {str(e)}")
            print("\nStreaming completed")

        except httpx.ConnectError as e:
            print(f"Connection Error: FastAPI server is not running at {base_url}")
            print("Please make sure to start the server with:")
            print("uvicorn app:app --reload")
            raise
        except Exception as e:
            print(f"Error during API test: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(test_api()) 