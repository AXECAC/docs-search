from pydantic import BaseModel
from uuid import UUID


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
    upload_date: datetime
    last_edited: datetime
    extension: str | None = None
    size_bytes: int | None = None
    description: str | None = None
    is_available_to: list[UUID] | None = None

    class Config:
        from_attributes = True


class DocumentUpdateRequest(BaseModel):
    title: str | None = None
    author: str | None = None
    description: str | None = None
    is_available_to: list[UUID] | None = None


class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    keywords: list[str] | None = None
    language: str | None = None

    class Config:
        from_attributes = True
