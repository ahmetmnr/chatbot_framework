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

async def get_test_user(db: AsyncSession = Depends(get_db)) -> User:
    """Geçici olarak test kullanıcısını döndürür"""
    query = select(User).where(User.username == 'test_user')
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # Test kullanıcısı yoksa oluştur
        user = User(
            id=str(uuid.uuid4()),
            username='test_user',
            email='test@example.com'
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user

# İleride gerçek auth sistemi eklendiğinde bu fonksiyon değiştirilecek
get_current_user = get_test_user 