# Path: chatbot_framework/app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from routers import assistants
import os

app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dosyaları sunmak için
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Routers
app.include_router(assistants.router)

@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")
