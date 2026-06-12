from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
import uuid
import os
import shutil

from app.database import get_db
from app.models import User, Document, Chunk
from app.schemas import (
    DocumentResponse, DocumentUploadResponse, DocumentUpdateRequest,
    ChunkResponse, SearchRequest, SearchResultItem,
)
from app.auth import get_current_user
from app.document_processor import process_document
from app.qdrant_client import delete_chunks_by_document
from app.search import hybrid_search

router = APIRouter(prefix="/documents", tags=["documents"])


UPLOAD_DIR = "uploads/raw"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    author: str | None = Form(None),
    description: str | None = Form(None),
    is_available_to: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    document_id = uuid.uuid4()
    
    # Обработка is_available_to (парсинг из строки, разделенной запятыми)
    available_users = []
    if is_available_to:
        for uid in is_available_to.split(","):
            uid = uid.strip()
            if uid:
                try:
                    uuid.UUID(uid)
                    available_users.append(uid)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid UUID format: {uid}")
    
    # Определение расширения
    filename = file.filename or ""
    _, ext = os.path.splitext(filename)
    extension = ext.lstrip(".").lower() if ext else None

    # Сохранение файла на диск
    file_path = os.path.join(UPLOAD_DIR, f"{document_id}.{extension}" if extension else str(document_id))
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            size_bytes = len(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Создание записи в БД
    doc_title = title or filename
    document = Document(
        id=document_id,
        title=doc_title,
        author=author,
        uploader_id=current_user.id,
        extension=extension,
        size_bytes=size_bytes,
        description=description,
        file_path=file_path,
        is_available_to=available_users if available_users else None
    )
    
    db.add(document)
    await db.commit()

    # Запуск фоновой задачи для парсинга и векторизации
    background_tasks.add_task(process_document, document_id=str(document_id), file_path=file_path)

    return DocumentUploadResponse(document_id=document_id, status="processing")


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Document)
    if current_user.role != "admin":
        # Обычный пользователь видит свои документы и те, что ему расшарены
        query = query.where(
            or_(
                Document.uploader_id == current_user.id,
                Document.is_available_to.has_key(str(current_user.id))
            )
        )
    
    result = await db.execute(query)
    documents = result.scalars().all()
    return documents


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if current_user.role != "admin" and document.uploader_id != current_user.id:
        if not document.is_available_to or str(current_user.id) not in document.is_available_to:
            raise HTTPException(status_code=403, detail="Access denied")
            
    return document


@router.get("/{doc_id}/chunks", response_model=list[ChunkResponse])
async def get_document_chunks(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Сначала проверяем доступ к самому документу
    doc_result = await db.execute(select(Document).where(Document.id == doc_id))
    document = doc_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if current_user.role != "admin" and document.uploader_id != current_user.id:
        if not document.is_available_to or str(current_user.id) not in document.is_available_to:
            raise HTTPException(status_code=403, detail="Access denied")
            
    # Загружаем чанки
    chunk_result = await db.execute(
        select(Chunk).where(Chunk.document_id == doc_id).order_by(Chunk.chunk_index)
    )
    return chunk_result.scalars().all()


@router.put("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: uuid.UUID,
    request: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if current_user.role != "admin" and document.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner or an admin can update this document")
        
    if request.title is not None:
        document.title = request.title
    if request.author is not None:
        document.author = request.author
    if request.description is not None:
        document.description = request.description
    if request.is_available_to is not None:
        # Для обновления передаём список как есть. Если список пустой, сохраняем None.
        document.is_available_to = [str(u) for u in request.is_available_to] if request.is_available_to else None
        
    await db.commit()
    await db.refresh(document)
    return document


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if current_user.role != "admin" and document.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner or an admin can delete this document")
        
    # Удаление файла с диска
    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            # Логируем, но продолжаем удаление из БД
            print(f"Failed to delete file {document.file_path}: {e}")
            
    # Удаление векторов из Qdrant
    delete_chunks_by_document(str(doc_id))
    
    # Удаление из БД (связанные чанки удалятся каскадно)
    await db.delete(document)
    await db.commit()
    
    return {"status": "deleted"}


@router.post("/search", response_model=list[SearchResultItem])
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Гибридный поиск по документам пользователя.
    Комбинирует семантический поиск (Qdrant) и поиск по ключевым словам (PostgreSQL).
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")
    results = await hybrid_search(
        query=request.query,
        current_user=current_user,
        db=db,
        top_k=request.top_k,
    )
    return results
