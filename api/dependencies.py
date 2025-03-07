from typing import Dict
from core.models.assistant import Assistant
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.database.models import User
import uuid

# Global assistants dictionary
assistants: Dict[str, Assistant] = {}

def get_assistant(name: str) -> Assistant:
    """Get assistant by name or raise 404"""
    if name not in assistants:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistants[name] 

# Auth router'ındaki gerçek current_user fonksiyonunu import ediyoruz
from routers.auth import get_current_user

# Bağımlılığı gerçek auth sistemine yönlendiriyoruz
get_current_user = get_current_user 