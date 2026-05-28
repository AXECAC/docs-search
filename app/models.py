from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
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
    is_available_to = Column(JSON)   # список ID пользователей

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    text = Column(String)
    keywords = Column(JSON)   # список строк
    language = Column(String)
    start_char = Column(Integer)
    end_char = Column(Integer)