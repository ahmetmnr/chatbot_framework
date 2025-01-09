# Path: chatbot_framework/app.py
from fastapi import FastAPI
from dotenv import load_dotenv
from routers import assistants_router, rag_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

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

# Statik dosyaları doğru şekilde yapılandır
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_spa():
    return FileResponse("frontend/index.html")
