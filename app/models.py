import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB  # <-- Импортируем JSONB
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    author = Column(String)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    upload_date = Column(DateTime, default=datetime.utcnow)
    last_edited = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extension = Column(String)
    size_bytes = Column(BigInteger)
    description = Column(String)
    file_path = Column(String)
    is_available_to = Column(JSONB)  # список ID пользователей, имеющих доступ

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    text = Column(String)
    keywords = Column(JSONB)       # список ключевых слов (строк)
    language = Column(String)
    start_char = Column(Integer)
    end_char = Column(Integer)

# Индексы для производительности
Index("idx_chunks_document_id", Chunk.document_id)
Index(
    "idx_chunks_keywords_gin",
    Chunk.keywords,
    postgresql_using="gin",
    postgresql_ops={"keywords": "jsonb_ops"}
)