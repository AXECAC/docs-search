# Docs search
<!-- здесь должно быть описание проекта -->

## Зависимости и их установка
### Ubuntu
```bash
sudo apt update
sudo apt install -y build-essential pkg-config clang llvm-dev libclang-dev \
                    libleptonica-dev libtesseract-dev tesseract-ocr \
                    tesseract-ocr-rus tesseract-ocr-eng python3 python3-pip
```

### Arch Linux
```bash
sudo pacman -Syu --needed --noconfirm build-essential pkgconf clang llvm \
                                      leptonica tesseract tesseract-data-rus \
                                      tesseract-data-eng python-pip
```

- maturin:
  ```bash
  # Запускаете .venv
  pip install -r ./requirements.txt
  ```
## Как запускать? (работа только в .venv окружении)

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Запуск инфраструктуры (PostgreSQL + Qdrant)
```bash
docker-compose up -d postgres qdrant
```

### 3. Применение миграций базы данных (Alembic)
```bash
# При первом развёртывании или после `git pull` с новыми миграциями:
alembic upgrade head
```

### 4. Запуск приложения
```bash
# Загрузить переменные окружения и запустить сервер:
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Фронтенд доступен по адресу: http://localhost:8000/ui/

---

## Работа с миграциями (Alembic)

Alembic управляет схемой базы данных. Это позволяет всей команде синхронизировать изменения в структуре БД.

### Создать новую миграцию после изменения `app/models.py`
```bash
alembic revision --autogenerate -m "описание_изменений"
```

### Применить все ожидающие миграции
```bash
alembic upgrade head
```

### Откатить последнюю миграцию
```bash
alembic downgrade -1
```

### Проверить текущее состояние БД
```bash
alembic current   # текущая версия
alembic check     # есть ли незаписанные изменения
alembic history   # история миграций
```
