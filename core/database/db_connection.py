from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLAlchemy async engine
DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/chatbot_db"
engine = create_async_engine(DATABASE_URL, echo=True)

# Session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency to get DB sessions
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

__all__ = ['Base', 'get_db', 'engine', 'async_session']
