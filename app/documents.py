from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, cast, String
import mimetypes
import uuid
import os

from app.database import get_db
from app.models import User, Document, Chunk, user_groups
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


# ──────────────────────────────────────────
# Вспомогательная функция проверки доступа
# ──────────────────────────────────────────

async def check_document_access(document: Document, current_user: User, db: AsyncSession) -> bool:
    """
    Возвращает True если пользователь имеет доступ к документу.
    Логика:
      - Владелец документа → всегда есть доступ.
      - Admin → всегда есть доступ.
      - Оба списка пусты (is_available_to=None и available_to_groups=None) → публичный, доступ есть.
      - ID пользователя в is_available_to → доступ есть.
      - Пользователь состоит в группе из available_to_groups → доступ есть.
    """
    if str(document.uploader_id) == str(current_user.id):
        return True
    if current_user.role == "admin":
        return True

    both_empty = (
        (not document.is_available_to or document.is_available_to == 'null')
        and (not document.available_to_groups or document.available_to_groups == 'null')
    )
    if both_empty:
        return True

    if document.is_available_to and str(current_user.id) in document.is_available_to:
        return True

    if document.available_to_groups:
        user_group_ids = await _get_user_group_ids(current_user.id, db)
        if any(gid in document.available_to_groups for gid in user_group_ids):
            return True

    return False


async def _get_user_group_ids(user_id: uuid.UUID, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(user_groups.c.group_id).where(user_groups.c.user_id == user_id)
    )
    return [str(row[0]) for row in result.fetchall()]


# ──────────────────────────────────────────
# Upload
# ──────────────────────────────────────────

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    author: str | None = Form(None),
    description: str | None = Form(None),
    is_available_to: str | None = Form(None),      # строка UUID через запятую
    available_to_groups: str | None = Form(None),  # строка UUID через запятую
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    document_id = uuid.uuid4()

    # Парсинг is_available_to
    available_users: list[str] = []
    if is_available_to:
        for uid in is_available_to.split(","):
            uid = uid.strip()
            if uid:
                try:
                    uuid.UUID(uid)
                    available_users.append(uid)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid user UUID: {uid}")

    # Парсинг available_to_groups
    # Обычный пользователь может назначать только группы, в которых сам состоит
    available_groups: list[str] = []
    if available_to_groups:
        raw_groups = [g.strip() for g in available_to_groups.split(",") if g.strip()]
        if current_user.role != "admin":
            user_group_ids = await _get_user_group_ids(current_user.id, db)
            # Фильтруем — только свои группы
            raw_groups = [g for g in raw_groups if g in user_group_ids]
        for gid in raw_groups:
            try:
                uuid.UUID(gid)
                available_groups.append(gid)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid group UUID: {gid}")

    # Расширение и сохранение файла
    filename = file.filename or ""
    _, ext = os.path.splitext(filename)
    extension = ext.lstrip(".").lower() if ext else None

    file_path = os.path.join(UPLOAD_DIR, f"{document_id}.{extension}" if extension else str(document_id))
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            size_bytes = len(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Запись в БД
    document = Document(
        id=document_id,
        title=title or filename,
        author=author,
        uploader_id=current_user.id,
        extension=extension,
        size_bytes=size_bytes,
        description=description,
        file_path=file_path,
        is_available_to=available_users if available_users else None,
        available_to_groups=available_groups if available_groups else None,
    )

    db.add(document)
    await db.commit()

    background_tasks.add_task(process_document, document_id=str(document_id), file_path=file_path)

    return DocumentUploadResponse(document_id=document_id, status="processing")


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────

async def _enrich_with_uploader(document: Document, db: AsyncSession) -> DocumentResponse:
    """Добавляет имя загрузчика к ответу документа."""
    uploader_username = None
    if document.uploader_id:
        result = await db.execute(select(User).where(User.id == document.uploader_id))
        uploader = result.scalar_one_or_none()
        if uploader:
            uploader_username = uploader.username
    return DocumentResponse(
        id=document.id,
        title=document.title,
        author=document.author,
        uploader_id=document.uploader_id,
        uploader_username=uploader_username,
        upload_date=document.upload_date,
        last_edited=document.last_edited,
        extension=document.extension,
        size_bytes=document.size_bytes,
        description=document.description,
        is_available_to=document.is_available_to,
        available_to_groups=document.available_to_groups,
    )


# ──────────────────────────────────────────
# List / Get
# ──────────────────────────────────────────

@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == "admin":
        result = await db.execute(select(Document))
        docs = result.scalars().all()
    else:
        # Для обычных пользователей учитываем и группы
        user_group_ids = await _get_user_group_ids(current_user.id, db)

        group_conditions = [
            Document.available_to_groups.has_key(gid)
            for gid in user_group_ids
        ]

        query = select(Document).where(
            or_(
                Document.uploader_id == current_user.id,
                # Публичный — оба списка пусты
                and_(
                    or_(Document.is_available_to.is_(None), cast(Document.is_available_to, String).in_(('null', '[]'))),
                    or_(Document.available_to_groups.is_(None), cast(Document.available_to_groups, String).in_(('null', '[]')))
                ),
                # Явный доступ пользователю
                Document.is_available_to.has_key(str(current_user.id)),
                # Доступ через группу
                *group_conditions,
            )
        )
        result = await db.execute(query)
        docs = result.scalars().all()

    return [await _enrich_with_uploader(doc, db) for doc in docs]


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

    if not await check_document_access(document, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")

    return await _enrich_with_uploader(document, db)


# ──────────────────────────────────────────
# Update
# ──────────────────────────────────────────

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
        document.is_available_to = [str(u) for u in request.is_available_to] if request.is_available_to else None
    if request.available_to_groups is not None:
        # Проверяем права: обычный пользователь — только свои группы
        if current_user.role != "admin":
            user_group_ids = await _get_user_group_ids(current_user.id, db)
            filtered = [str(g) for g in request.available_to_groups if str(g) in user_group_ids]
        else:
            filtered = [str(g) for g in request.available_to_groups]
        document.available_to_groups = filtered if filtered else None

    await db.commit()
    await db.refresh(document)
    return document


# ──────────────────────────────────────────
# Delete
# ──────────────────────────────────────────

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

    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            print(f"Failed to delete file {document.file_path}: {e}")

    delete_chunks_by_document(str(doc_id))
    await db.delete(document)
    await db.commit()

    return {"status": "deleted"}


# ──────────────────────────────────────────
# Search
# ──────────────────────────────────────────

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


# ──────────────────────────────────────────
# File Content (Preview / Download)
# ──────────────────────────────────────────

INLINE_EXTENSIONS = {"pdf", "txt", "png", "jpg", "jpeg", "gif", "webp", "svg"}


@router.get("/{doc_id}/content")
async def get_document_content(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Возвращает оригинальный файл документа.
    - PDF, TXT, изображения — отдаются inline (отображаются в браузере).
    - DOCX, XLSX, PPTX и пр. — отдаются как вложение (скачивание).
    Доступ проверяется по правам пользователя, включая группы.
    """
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if not await check_document_access(document, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    ext = (document.extension or "").lstrip(".").lower()
    mime_type, _ = mimetypes.guess_type(document.file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    disposition = "inline" if ext in INLINE_EXTENSIONS else "attachment"
    filename = os.path.basename(document.file_path)

    from urllib.parse import quote

    return FileResponse(
        path=document.file_path,
        media_type=mime_type,
        filename=filename,
        content_disposition_type=disposition,
        headers={
            "X-Document-Title": quote(document.title or filename),
        },
    )
