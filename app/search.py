"""
app/search.py — Гибридный поиск: семантический (Qdrant) + по ключевым словам (PostgreSQL).
"""
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, cast, String

from app.models import User, Document, Chunk, user_groups
from app.qdrant_client import semantic_search
from app.embeddings import get_embedding
from app.schemas import SearchResultItem
from sqlalchemy.future import select

logger = logging.getLogger(__name__)


def _get_accessible_doc_ids(documents: list[Document]) -> set[str]:
    return {str(doc.id) for doc in documents}


async def hybrid_search(
    query: str,
    current_user: User,
    db: AsyncSession,
    top_k: int = 10,
) -> List[SearchResultItem]:
    """
    Гибридный поиск:
    1. Получаем список документов, доступных пользователю.
    2. Семантический поиск в Qdrant по вектору запроса.
    3. Поиск по ключевым словам в PostgreSQL по чанкам этих документов.
    4. Объединяем, дедублицируем, сортируем по score и возвращаем top_k.
    """

    # ── 1. Список доступных документов ───────────────────────────────────
    if current_user.role == "admin":
        doc_result = await db.execute(select(Document))
    else:
        # Получаем группы пользователя
        gid_result = await db.execute(
            select(user_groups.c.group_id).where(user_groups.c.user_id == current_user.id)
        )
        user_group_ids = [str(row[0]) for row in gid_result.fetchall()]

        group_conditions = [
            Document.available_to_groups.has_key(gid)
            for gid in user_group_ids
        ]

        doc_query = select(Document).where(
            or_(
                Document.uploader_id == current_user.id,
                and_(
                    or_(Document.is_available_to.is_(None), cast(Document.is_available_to, String).in_(('null', '[]'))),
                    or_(Document.available_to_groups.is_(None), cast(Document.available_to_groups, String).in_(('null', '[]')))
                ),
                Document.is_available_to.has_key(str(current_user.id)),
                *group_conditions,
            )
        )
        doc_result = await db.execute(doc_query)

    accessible_docs = doc_result.scalars().all()
    accessible_doc_ids = _get_accessible_doc_ids(accessible_docs)
    doc_lookup = {str(doc.id): doc for doc in accessible_docs}

    if not accessible_doc_ids:
        return []

    # ── 2. Семантический поиск в Qdrant ──────────────────────────────────
    query_embedding = get_embedding(query)
    qdrant_results = semantic_search(query_embedding, top_k=top_k * 3)

    # Фильтруем по доступным документам
    semantic_hits: dict[str, dict] = {}
    for hit in qdrant_results:
        doc_id = hit.get("document_id")
        chunk_id = str(hit.get("id", ""))
        if doc_id in accessible_doc_ids:
            semantic_hits[chunk_id] = {
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "text": hit.get("text", ""),
                "keywords": hit.get("keywords", []),
                "score": float(hit.get("score", 0.0)),
            }

    # ── 3. Поиск по ключевым словам в PostgreSQL ─────────────────────────
    # Извлекаем слова из запроса (≥3 символа) для простого keyword-поиска
    query_words = [w.lower() for w in query.split() if len(w) >= 3]

    keyword_hits: dict[str, dict] = {}
    if query_words:
        # Ищем чанки, у которых хотя бы одно ключевое слово содержит слово из запроса
        chunk_query = select(Chunk).where(
            Chunk.document_id.in_([
                # UUID-объекты для корректного сравнения
                doc.id for doc in accessible_docs
            ])
        )
        chunk_result = await db.execute(chunk_query)
        all_chunks = chunk_result.scalars().all()

        for chunk in all_chunks:
            chunk_kw_list = chunk.keywords or []
            chunk_kw_lower = [kw.lower() for kw in chunk_kw_list]
            chunk_text_lower = (chunk.text or "").lower()

            # Считаем количество совпадений
            matches = 0
            for word in query_words:
                if any(word in kw for kw in chunk_kw_lower):
                    matches += 1
                elif word in chunk_text_lower:
                    matches += 0.5  # частичное совпадение в тексте

            if matches > 0:
                kw_score = matches / len(query_words)  # нормализуем в [0..1]
                chunk_id = str(chunk.id)
                keyword_hits[chunk_id] = {
                    "chunk_id": chunk_id,
                    "document_id": str(chunk.document_id),
                    "text": chunk.text or "",
                    "keywords": chunk.keywords or [],
                    "score": kw_score * 0.5,  # масштабируем, чтобы не перекрыть семантику
                }

    # ── 4. Объединение результатов ────────────────────────────────────────
    merged: dict[str, dict] = {}

    for chunk_id, hit in semantic_hits.items():
        merged[chunk_id] = dict(hit)

    for chunk_id, hit in keyword_hits.items():
        if chunk_id in merged:
            # Если чанк найден обоими методами — суммируем score
            merged[chunk_id]["score"] += hit["score"]
        else:
            merged[chunk_id] = dict(hit)

    # ── 5. Обогащаем заголовком и расширением документа ──────────────────
    results: List[SearchResultItem] = []
    for hit in merged.values():
        doc = doc_lookup.get(hit["document_id"])
        if doc is None:
            continue
        results.append(SearchResultItem(
            chunk_id=hit["chunk_id"],
            document_id=hit["document_id"],
            document_title=doc.title,
            extension=doc.extension,
            text=hit["text"],
            keywords=hit["keywords"],
            score=round(hit["score"], 4),
        ))

    # Сортируем по убыванию релевантности и обрезаем до top_k
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]