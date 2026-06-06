from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Подключение к Qdrant
qdrant = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "chunks"
VECTOR_SIZE = 312

def ensure_collection():
    """Создаёт коллекцию в Qdrant, если её нет"""
    try:
        collections = qdrant.get_collections().collections
        if not any(c.name == COLLECTION_NAME for c in collections):
            qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Collection '{COLLECTION_NAME}' created")
        else:
            logger.debug(f"Collection '{COLLECTION_NAME}' already exists")
    except Exception as e:
        logger.error(f"Failed to ensure collection: {e}")

def index_chunk(
    chunk_id: str,
    document_id: str,
    chunk_index: int,
    text: str,
    keywords: List[str],
    language: str,
    embedding: List[float]
) -> bool:
    """Сохраняет вектор и метаданные чанка в Qdrant"""
    ensure_collection()
    try:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "text": text,
                        "keywords": keywords,
                        "language": language
                    }
                )
            ]
        )
        logger.debug(f"Indexed chunk {chunk_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to index chunk {chunk_id}: {e}")
        return False

def semantic_search(query_embedding: List[float], top_k: int = 10) -> List[Dict]:
    """Семантический поиск по вектору (KNN)"""
    ensure_collection()
    try:
        # Используем query_points вместо search (для новых версий Qdrant)
        results = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=top_k,
            with_payload=True
        )
        return [
            {
                "id": hit.id,
                "score": hit.score,
                **hit.payload
            }
            for hit in results.points
        ]
    except AttributeError:
        # Для старых версий Qdrant (fallback)
        try:
            results = qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True
            )
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    **hit.payload
                }
                for hit in results
            ]
        except Exception as e2:
            logger.error(f"Both search methods failed: {e2}")
            return []
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []

def delete_chunks_by_document(document_id: str) -> bool:
    """Удаляет все чанки документа из Qdrant"""
    try:
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id)
                        )
                    ]
                )
            )
        )
        logger.info(f"Deleted chunks for document {document_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete chunks for document {document_id}: {e}")
        return False

def delete_all_chunks():
    """Очищает всю коллекцию (для тестов)"""
    try:
        qdrant.delete_collection(COLLECTION_NAME)
        logger.info("Collection deleted")
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")

def get_chunk_count() -> int:
    """Возвращает количество точек в коллекции"""
    try:
        ensure_collection()
        info = qdrant.get_collection(COLLECTION_NAME)
        return info.points_count
    except Exception as e:
        logger.error(f"Failed to get chunk count: {e}")
        return 0