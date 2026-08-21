import os
import json
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import ChatRequest
from app.auth import get_current_user
from app.search import hybrid_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

async def generate_chat_response(query: str, current_user: User, db: AsyncSession):
    # 1. Поиск контекста
    try:
        search_results = await hybrid_search(
            query=query,
            current_user=current_user,
            db=db,
            top_k=5
        )
    except Exception as e:
        logger.error(f"Error during search: {e}")
        yield json.dumps({"type": "error", "content": "Failed to retrieve context."}) + "\n"
        return

    # Отправка источников первым пакетом
    sources = [
        {
            "document_id": r.document_id,
            "document_title": r.document_title,
            "extension": r.extension,
            "score": r.score
        } for r in search_results
    ]
    # Дедупликация источников для UI
    unique_sources = list({s["document_id"]: s for s in sources}.values())
    
    yield json.dumps({"type": "sources", "sources": unique_sources}) + "\n"

    # 2. Формирование промпта
    if not search_results:
        context_text = "Нет релевантных документов для этого запроса."
    else:
        context_text = "\n\n".join(
            f"--- Документ: {r.document_title} ---\n{r.text}"
            for r in search_results
        )

    system_prompt = (
        "Вы - корпоративный ИИ-ассистент. Ваша задача - отвечать на вопросы пользователя, "
        "основываясь ТОЛЬКО на предоставленном контексте из корпоративных документов. "
        "Если в контексте нет ответа на вопрос, честно скажите, что не знаете. "
        "Не придумывайте информацию. Отвечайте на русском языке.\n\n"
        f"КОНТЕКСТ:\n{context_text}"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "stream": True
    }

    # 3. Отправка запроса в Ollama и стриминг
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{OLLAMA_HOST}/api/chat", json=payload, timeout=60.0) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield json.dumps({"type": "error", "content": f"Ollama error: {response.status_code} {error_text.decode()}"}) + "\n"
                    return
                
                async for chunk in response.aiter_lines():
                    if chunk:
                        try:
                            data = json.loads(chunk)
                            if "message" in data and "content" in data["message"]:
                                yield json.dumps({
                                    "type": "content", 
                                    "content": data["message"]["content"]
                                }) + "\n"
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse Ollama chunk: {chunk}")
    except httpx.RequestError as e:
        logger.error(f"Error communicating with Ollama: {e}")
        yield json.dumps({"type": "error", "content": "Ошибка связи с Ollama. Проверьте, запущен ли сервер."}) + "\n"


@router.post("")
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    return StreamingResponse(
        generate_chat_response(request.query, current_user, db),
        media_type="application/x-ndjson"
    )
