from app.qdrant_client import semantic_search, delete_chunks_by_document
from app.embeddings import get_embedding

async def search_by_query(query: str, top_k: int = 10):
    query_embedding = get_embedding(query)
    results = semantic_search(query_embedding, top_k)
    # results уже содержат payload с document_id, text, keywords и т.д.
    return results