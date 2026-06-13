"""
app/groups.py — управление группами доступа.
Создание/удаление групп и управление участниками — только для admin.
Просмотр списка групп — для всех авторизованных пользователей.
"""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func

from app.database import get_db
from app.models import User, Group, user_groups
from app.schemas import GroupCreate, GroupResponse, GroupMemberAdd, UserSearchResult
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groups", tags=["groups"])


# ──────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_user_group_ids(user_id: uuid.UUID, db: AsyncSession) -> list[str]:
    """Возвращает список строковых ID групп, в которых состоит пользователь."""
    result = await db.execute(
        select(user_groups.c.group_id).where(user_groups.c.user_id == user_id)
    )
    return [str(row[0]) for row in result.fetchall()]


# ──────────────────────────────────────────
# Группы CRUD
# ──────────────────────────────────────────

@router.get("", response_model=list[GroupResponse])
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список всех групп. Доступен для всех авторизованных пользователей."""
    result = await db.execute(select(Group).order_by(Group.name))
    groups = result.scalars().all()

    # Подсчитываем количество участников для каждой группы
    group_list = []
    for g in groups:
        count_result = await db.execute(
            select(func.count()).select_from(user_groups).where(user_groups.c.group_id == g.id)
        )
        count = count_result.scalar() or 0
        group_list.append(GroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            created_at=g.created_at,
            member_count=count,
        ))
    return group_list


@router.post("", response_model=GroupResponse)
async def create_group(
    data: GroupCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Создать новую группу. Только для admin."""
    existing = await db.execute(select(Group).where(Group.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Группа с таким именем уже существует")

    group = Group(
        id=uuid.uuid4(),
        name=data.name,
        description=data.description,
        created_by=current_user.id,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        member_count=0,
    )


@router.delete("/{group_id}")
async def delete_group(
    group_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Удалить группу. Только для admin."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    await db.commit()
    return {"status": "deleted"}


# ──────────────────────────────────────────
# Участники групп
# ──────────────────────────────────────────

@router.get("/{group_id}/members", response_model=list[UserSearchResult])
async def get_group_members(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список участников группы."""
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    if not group_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Group not found")

    stmt = (
        select(User)
        .join(user_groups, User.id == user_groups.c.user_id)
        .where(user_groups.c.group_id == group_id)
        .order_by(User.username)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{group_id}/members")
async def add_members(
    group_id: uuid.UUID,
    data: GroupMemberAdd,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Добавить пользователей в группу. Только для admin."""
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    if not group_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Group not found")

    added = []
    for user_id in data.user_ids:
        user_result = await db.execute(select(User).where(User.id == user_id))
        if not user_result.scalar_one_or_none():
            continue

        existing = await db.execute(
            select(user_groups).where(
                user_groups.c.user_id == user_id,
                user_groups.c.group_id == group_id,
            )
        )
        if not existing.first():
            await db.execute(
                user_groups.insert().values(user_id=user_id, group_id=group_id)
            )
            added.append(str(user_id))

    await db.commit()
    return {"added": added}


@router.delete("/{group_id}/members/{user_id}")
async def remove_member(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Убрать пользователя из группы. Только для admin."""
    await db.execute(
        delete(user_groups).where(
            user_groups.c.user_id == user_id,
            user_groups.c.group_id == group_id,
        )
    )
    await db.commit()
    return {"status": "removed"}
