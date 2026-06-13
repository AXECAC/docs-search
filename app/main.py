"""
app/main.py — точка входа FastAPI-приложения.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import engine
from app.embeddings import load_model, get_embedding_dimension

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────
# Lifespan: инициализация при старте
# ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Проверяем подключение к БД
    # Таблицами управляет Alembic — запустите `alembic upgrade head` перед стартом
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    # 2. Загружаем модель эмбеддингов
    load_model()
    logger.info(f"Embedding model loaded, dimension: {get_embedding_dimension()}")

    yield
    # (teardown при завершении — при необходимости добавить сюда)


# ──────────────────────────────────────────
# Приложение
# ──────────────────────────────────────────

app = FastAPI(
    title="Docs Search API",
    description="Корпоративная RAG-система для работы с приватными документами",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — разрешаем фронтенд на localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────
# Роутеры
# ──────────────────────────────────────────

from app.auth import router as auth_router  # noqa: E402
from app.documents import router as docs_router
from app.chat import router as chat_router

app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(chat_router)


# ──────────────────────────────────────────
# Системные эндпоинты
# ──────────────────────────────────────────

@app.get("/api", tags=["system"])
def root():
    return {"status": "ok", "message": "Docs Search API is running"}

app.mount("/ui", StaticFiles(directory="front-end", html=True), name="static")


@app.get("/health", tags=["system"])
def health():
    db_url = os.getenv("DATABASE_URL", "not set")
    # Скрываем пароль из URL для безопасного логирования
    safe_url = db_url.split("@")[-1] if "@" in db_url else db_url
    return {"status": "healthy", "database": safe_url}