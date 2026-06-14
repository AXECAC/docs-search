from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


# ──────────────────────────────────────────
# Устаревшие схемы (оставляем для совместимости)
# ──────────────────────────────────────────

class ParseResponse(BaseModel):
    file_id: str
    original_filename: str
    parsed_file_path: str | None = None
    status: str


# ──────────────────────────────────────────
# Аутентификация
# ──────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    """Возвращается при логине и обновлении токена."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Тело запроса POST /auth/refresh."""
    refresh_token: str


class UserResponse(BaseModel):
    """Публичное представление пользователя."""
    id: UUID
    username: str
    role: str

    class Config:
        from_attributes = True


# ──────────────────────────────────────────
# Управление документами
# ──────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: UUID
    status: str


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    author: str | None = None
    uploader_id: UUID | None = None
    uploader_username: str | None = None
    upload_date: datetime
    last_edited: datetime
    extension: str | None = None
    size_bytes: int | None = None
    description: str | None = None
    is_available_to: list[str] | None = None
    available_to_groups: list[str] | None = None

    class Config:
        from_attributes = True


class PaginatedDocuments(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    pages: int
    page_size: int


class DocumentUpdateRequest(BaseModel):
    title: str | None = None
    author: str | None = None
    description: str | None = None
    is_available_to: list[UUID] | None = None
    available_to_groups: list[UUID] | None = None


class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    keywords: list[str] | None = None
    language: str | None = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────
# Поиск
# ──────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    extension: str | None = None
    text: str
    keywords: list[str] | None = None
    score: float


# ──────────────────────────────────────────
# Чат (RAG)
# ──────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str


# ──────────────────────────────────────────
# Группы и управление доступом
# ──────────────────────────────────────────

class GroupCreate(BaseModel):
    name: str
    description: str | None = None


class GroupMemberAdd(BaseModel):
    user_ids: list[UUID]


class GroupResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    member_count: int | None = None

    class Config:
        from_attributes = True


class UserSearchResult(BaseModel):
    id: UUID
    username: str
    role: str

    class Config:
        from_attributes = True
