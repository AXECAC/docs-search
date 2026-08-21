"""
Аутентификация: JWT (access + refresh), хэширование паролей,
зависимости FastAPI и роутер /auth.
"""
import os
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.schemas import (
    UserRegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    UserSearchResult,
)
import uuid

logger = logging.getLogger(__name__)

# ------------------------------------------
# Конфигурация из переменных окружения
# ------------------------------------------

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "60"))
REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

if not SECRET_KEY:
    logger.warning(
        "JWT_SECRET_KEY not set in environment! Using insecure dev fallback."
    )
    SECRET_KEY = "dev-secret-key-please-set-in-env"

if not REFRESH_SECRET_KEY:
    logger.warning(
        "JWT_REFRESH_SECRET_KEY not set in environment! Using insecure dev fallback."
    )
    REFRESH_SECRET_KEY = "dev-refresh-secret-please-set-in-env"

# ------------------------------------------
# Хэширование паролей (bcrypt напрямую, без passlib)
# ------------------------------------------

def get_password_hash(password: str) -> str:
    """Возвращает bcrypt-хэш пароля."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнивает открытый пароль с bcrypt-хэшем."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ------------------------------------------
# JWT - создание и декодирование
# ------------------------------------------

def create_access_token(data: dict) -> str:
    """
    Создаёт короткоживущий access-токен.
    TTL = JWT_ACCESS_EXPIRE_MINUTES (по умолчанию 60 мин).
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Создаёт долгоживущий refresh-токен.
    TTL = JWT_REFRESH_EXPIRE_DAYS (по умолчанию 7 дней).
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Декодирует и валидирует access-токен.
    Выбрасывает JWTError при невалидном или истёкшем токене.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Wrong token type")
    return payload


def decode_refresh_token(token: str) -> dict:
    """
    Декодирует и валидирует refresh-токен.
    Выбрасывает JWTError при невалидном или истёкшем токене.
    """
    payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "refresh":
        raise JWTError("Wrong token type")
    return payload


# ------------------------------------------
# FastAPI Dependencies
# ------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: извлекает текущего пользователя из access-токена.
    Выбрасывает 401, если токен невалиден или пользователь не найден.
    """
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise _CREDENTIALS_EXCEPTION
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency: проверяет, что текущий пользователь - admin.
    Выбрасывает 403, если нет.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ------------------------------------------
# Роутер /auth
# ------------------------------------------

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Регистрация нового пользователя.
    - Если username совпадает с ADMIN_USERNAME и пароль совпадает с ADMIN_PASSWORD -
      роль будет 'admin'.
    - Иначе - роль 'user'.
    """
    # Проверяем уникальность имени
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Определяем роль
    role = "user"
    if (
        ADMIN_USERNAME
        and body.username == ADMIN_USERNAME
        and body.password == ADMIN_PASSWORD
    ):
        role = "admin"

    user = User(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"Registered user '{user.username}' with role '{user.role}'")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Логин по username + password (OAuth2 form).
    Возвращает пару access_token + refresh_token.
    """
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {"sub": user.username}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Обновление токенов по refresh_token.
    Возвращает новую пару access_token + refresh_token.
    """
    try:
        payload = decode_refresh_token(body.refresh_token)
        username: str = payload.get("sub")
        if not username:
            raise JWTError("No subject")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Убедимся, что пользователь ещё существует в БД
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    token_data = {"sub": username}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Возвращает данные текущего авторизованного пользователя."""
    return current_user


@router.get("/users", response_model=list[UserSearchResult])
async def search_users(
    q: str | None = None,
    group_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Поиск пользователей. Только для admin.
    q        - фильтр по username (ILIKE)
    group_id - вернуть только членов определённой группы
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.models import user_groups

    stmt = select(User)
    if group_id:
        try:
            gid = uuid.UUID(group_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid group_id format")
        stmt = (
            stmt
            .join(user_groups, User.id == user_groups.c.user_id)
            .where(user_groups.c.group_id == gid)
        )
    if q:
        stmt = stmt.where(User.username.ilike(f"%{q}%"))

    result = await db.execute(stmt.order_by(User.username).limit(50))
    return result.scalars().all()
