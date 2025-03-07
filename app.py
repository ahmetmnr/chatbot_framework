# Path: chatbot_framework/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import assistants_router, rag_router, documents_router,auth
from core.database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from config.logger import app_logger

app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Conversation-Id"]  # Bu header'ın expose edildiğinden emin olun
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
app.include_router(assistants_router)
app.include_router(rag_router)
app.include_router(documents_router)

# Root endpoint - index.html'i serve et
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

# API root endpoint
@app.get("/api")
async def api_root():
    return {"message": "Welcome to AI Chat API"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    app_logger.error(
        "Global hata: %s - URL: %s",
        str(exc),
        request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
