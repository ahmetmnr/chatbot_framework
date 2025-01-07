# Path: chatbot_framework/app.py
from fastapi import FastAPI
from dotenv import load_dotenv
from routers import assistants_router, rag_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Chatbot Framework API",
    description="A modular framework for building chatbots with multiple LLMs and RAG systems",
    version="1.0.0"
)

# Include routers
app.include_router(assistants_router)
app.include_router(rag_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Chatbot Framework API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
