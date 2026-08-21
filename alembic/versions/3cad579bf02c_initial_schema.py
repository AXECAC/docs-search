"""initial_schema

Revision ID: 3cad579bf02c
Revises:
Create Date: 2026-06-14 00:11:48.436585

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3cad579bf02c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema: users, documents, chunks + indexes."""

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=True, server_default='user'),
    )

    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('uploader_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('upload_date', sa.DateTime(), nullable=True),
        sa.Column('last_edited', sa.DateTime(), nullable=True),
        sa.Column('extension', sa.String(), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('is_available_to', postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('keywords', postgresql.JSONB(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('start_char', sa.Integer(), nullable=True),
        sa.Column('end_char', sa.Integer(), nullable=True),
    )

    # Индексы
    op.create_index('idx_chunks_document_id', 'chunks', ['document_id'])
    op.create_index(
        'idx_chunks_keywords_gin',
        'chunks',
        ['keywords'],
        postgresql_using='gin',
        postgresql_ops={'keywords': 'jsonb_ops'},
    )


def downgrade() -> None:
    """Drop all tables and indexes."""
    op.drop_index('idx_chunks_keywords_gin', table_name='chunks')
    op.drop_index('idx_chunks_document_id', table_name='chunks')
    op.drop_table('chunks')
    op.drop_table('documents')
    op.drop_table('users')
