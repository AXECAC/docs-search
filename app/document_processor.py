# app/document_processor.py
import uuid
from app.database import AsyncSessionLocal
from app.models import Chunk
from app.qdrant_client import index_chunk
from app.embeddings import get_embedding
from app.keyword_extraction.paragraph_processor import ParagraphProcessor
from app.keyword_extraction.keyword_processor import KeywordProcessor
from app.keyword_extraction.language_detection import detect_language_simple
import logging

logger = logging.getLogger(__name__)

chunker = ParagraphProcessor(max_chunk_size=1000, overlap=200)
kw_processor = KeywordProcessor()

async def process_document(document_id: str, file_path: str, metadata: dict = None):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return

    chunks_data = chunker.process_paragraph(raw_text)
    if not chunks_data:
        logger.warning(f"No chunks generated for document {document_id}")
        return

    async with AsyncSessionLocal() as db:
        for idx, chunk_info in enumerate(chunks_data):
            chunk_text = chunk_info['text']
            language = detect_language_simple(chunk_text)
            
            keywords_with_scores = kw_processor.extract_keywords_from_text(
                chunk_text, language, top_n=5
            )
            keywords = [kw for kw, _ in keywords_with_scores]
            
            embedding = get_embedding(chunk_text)
            
            chunk_id = uuid.uuid4()
            chunk = Chunk(
                id=chunk_id,
                document_id=uuid.UUID(document_id),
                chunk_index=idx,
                text=chunk_text,
                keywords=keywords,
                language=language,
                start_char=chunk_info.get('start', 0),
                end_char=chunk_info.get('end', 0)
            )
            db.add(chunk)
            await db.flush()
            
            success = index_chunk(
                chunk_id=str(chunk_id),
                document_id=document_id,
                chunk_index=idx,
                text=chunk_text,
                keywords=keywords,
                language=language,
                embedding=embedding
            )
            if not success:
                logger.warning(f"Qdrant indexing failed for chunk {chunk_id}")
        
        await db.commit()
        logger.info(f"Document {document_id} processed: {len(chunks_data)} chunks")