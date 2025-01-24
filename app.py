# Path: chatbot_framework/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import assistants, auth
from core.database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Conversation-Id"]  # Conversation ID header'ını expose et
)

# Frontend dosyalarını serve et
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Tabloları oluştur
@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Routerları ekle
app.include_router(auth.router)
app.include_router(assistants.router)

# Root endpoint - index.html'i serve et
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

# API root endpoint
@app.get("/api")
async def api_root():
    return {"message": "Welcome to AI Chat API"}
