FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости системы для сборки
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY backend/requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY backend/app ./app
COPY backend/.env .env

# Копируем README, чтобы он был доступен RAG-движку внутри контейнера
# на той же относительной глубине, что и в локальной разработке.
COPY README.md ./README.md

# Открываем порт
EXPOSE 8000

# Запускаем сервер
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
