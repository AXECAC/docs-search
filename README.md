# Корпоративная RAG-система для работы с приватными документами

Docs Search - это корпоративная система для семантического поиска и ИИ-анализа документов. Проект использует FastAPI для бэкенда, Qdrant для векторного поиска, PostgreSQL для метаданных и пользователей, а также локальную языковую модель (`cointegrated/rubert-tiny2`) для создания эмбеддингов.

## Системные требования

- **ОС:** Linux (Ubuntu/Debian, Arch Linux и др.)
- **Среда:** Python 3.10+
- **Инфраструктура:** Docker и Docker Compose (для запуска баз данных PostgreSQL и Qdrant)

---

## Установка и первый запуск

Данная инструкция описывает развёртывание проекта для локальной разработки и тестирования, где базы данных работают в Docker-контейнерах, а сам FastAPI-сервер запускается напрямую в виртуальном окружении.

### 1. Установка системных зависимостей

Вам потребуются инструменты для компиляции и библиотеки OCR (Tesseract):

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y build-essential pkg-config clang llvm-dev libclang-dev \
                    libleptonica-dev libtesseract-dev tesseract-ocr \
                    tesseract-ocr-rus tesseract-ocr-eng python3 python3-pip python3-venv
```

**Arch Linux:**
```bash
sudo pacman -Syu --needed --noconfirm build-essential pkgconf clang llvm \
                                      leptonica tesseract tesseract-data-rus \
                                      tesseract-data-eng python-pip
```

### 2. Настройка виртуального окружения (Python)

Перейдите в директорию проекта, создайте и активируйте виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Установите все необходимые зависимости:
```bash
pip install -r requirements.txt
```

### 3. Конфигурация переменных окружения (`.env`)

Для работы приложению требуются ключи и настройки баз данных. Создайте в корне проекта файл `.env` со следующим содержимым:

```ini
# Доступы к PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=docs_db
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/docs_db

# Секретные ключи для JWT
JWT_SECRET_KEY=your_super_secret_key_here
JWT_REFRESH_SECRET_KEY=your_super_refresh_secret_here
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=7

# Учетные данные суперадминистратора
ADMIN_USERNAME=...
ADMIN_PASSWORD=...

# API Ключи для ИИ чата (если используются GigaChat/DeepSeek)
GIGACHAT_API_KEY=...
DEEPSEEK_API_KEY=...

# Интеграция локальной LLM через Ollama (опционально)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

*(Обязательно замените секретные ключи на надёжные значения в рабочей среде).*

### 4. Запуск баз данных (Docker)

Запустите PostgreSQL и Qdrant в фоне с помощью Docker Compose:

```bash
docker compose up -d
```
Эта команда создаст контейнеры `docs_postgres` (порт 5432) и `docs_qdrant` (порт 6333) и сохранит их данные в Docker Volumes, чтобы они не исчезли после перезапуска.

### 5. Применение миграций схемы БД

Чтобы создать необходимые таблицы в базе данных PostgreSQL, выполните миграции Alembic.
*(Убедитесь, что виртуальное окружение `.venv` активировано!)*

```bash
export $(grep -v '^#' .env | xargs)
alembic upgrade head
```

### 6. Запуск Backend сервера

Теперь всё готово для запуска основного приложения:

```bash
# Экспортируем переменные окружения и запускаем FastAPI
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Использование системы

- **Веб-интерфейс:** Откройте в браузере [http://localhost:8000/ui/](http://localhost:8000/ui/). 
- **Вход в систему:** Используйте логин `admin` и пароль `admin1234` (указанные в `.env`), чтобы получить права администратора.
- **API Документация (Swagger):** Доступна по адресу [http://localhost:8000/docs](http://localhost:8000/docs).

*Примечание: При первом запуске сервер скачает NLP-модель (`cointegrated/rubert-tiny2`), что может занять от нескольких секунд до пары минут в зависимости от скорости интернет-соединения.*

---

## Разработка: Работа с миграциями (Alembic)

Alembic используется для управления схемой базы данных. Это позволяет легко синхронизировать изменения таблиц.

**Создать новую миграцию** после изменения схемы в файле `app/models.py`:
```bash
alembic revision --autogenerate -m "описание_изменений"
```

**Применить все ожидающие миграции:**
```bash
alembic upgrade head
```

**Откатить последнюю миграцию:**
```bash
alembic downgrade -1
```

**Проверить текущее состояние:**
```bash
alembic current   # Текущая версия
alembic check     # Есть ли незафиксированные изменения
alembic history   # История миграций
```
