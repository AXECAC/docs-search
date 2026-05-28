import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Используем localhost вместо postgres (так как запускаем локально)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/docs_db")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session