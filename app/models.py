import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger, Index, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


# ──────────────────────────────────────────
# Ассоциативная таблица User ↔ Group
# ──────────────────────────────────────────
user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")

    groups = relationship("Group", secondary=user_groups, back_populates="members")


class Group(Base):
    __tablename__ = "groups"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("User", secondary=user_groups, back_populates="groups")


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
    is_available_to = Column(JSONB)       # список ID пользователей, имеющих доступ
    available_to_groups = Column(JSONB)   # список ID групп, имеющих доступ


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    text = Column(String)
    keywords = Column(JSONB)
    language = Column(String)
    start_char = Column(Integer)
    end_char = Column(Integer)


# Индексы для производительности
Index("idx_chunks_document_id", Chunk.document_id)
Index(
    "idx_chunks_keywords_gin",
    Chunk.keywords,
    postgresql_using="gin",
    postgresql_ops={"keywords": "jsonb_ops"},
)