FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего приложения
COPY ./app /app
COPY ./scripts /scripts

# Создание директории для кэша моделей
RUN mkdir -p /app/model_cache

# Установка PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8000

# Запуск: ждём БД, создаём таблицы, запускаем uvicorn
CMD ["sh", "-c", "python /scripts/wait_for_db.py && python /scripts/init_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]