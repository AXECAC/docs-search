import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем БД модули
from app.database import engine, Base
from app.models import *

async def init_db():
    async with engine.begin() as conn:
        # Удаляем все таблицы (для чистой инициализации)
        await conn.run_sync(Base.metadata.drop_all)
        # Создаём заново
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully")

if __name__ == "__main__":
    asyncio.run(init_db())