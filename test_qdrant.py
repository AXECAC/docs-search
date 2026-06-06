import asyncio
import uuid
from app.embeddings import get_embedding
from app.qdrant_client import index_chunk, semantic_search, get_chunk_count, delete_all_chunks

async def test():
    print("=== Testing Qdrant ===\n")
    
    # Очистка
    print("1. Cleaning up...")
    delete_all_chunks()
    print(f"   Chunks after cleanup: {get_chunk_count()}\n")
    
    # Индексация тестового чанка
    print("2. Indexing test chunk...")
    chunk_id = str(uuid.uuid4())
    text = "Нейронные сети и машинное обучение"
    emb = get_embedding(text)
    success = index_chunk(
        chunk_id=chunk_id,
        document_id="test-doc-123",
        chunk_index=0,
        text=text,
        keywords=["нейронные сети", "машинное обучение"],
        language="ru",
        embedding=emb
    )
    print(f"   Indexing success: {success}")
    print(f"   Chunks after index: {get_chunk_count()}\n")
    
    # Семантический поиск
    print("3. Semantic search...")
    query = "глубокое обучение"
    query_emb = get_embedding(query)
    results = semantic_search(query_emb, top_k=3)
    print(f"   Found {len(results)} results")
    for r in results:
        print(f"   - Score: {r.get('score', 0):.4f} | Text: {r.get('text', '')[:50]}...")
    
    print("\n✓ Test completed")

if __name__ == "__main__":
    asyncio.run(test())