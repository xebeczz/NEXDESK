# Backend — FastAPI + uvicorn
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code + alembic migrations.
COPY . .

# Runtime data volume (SQLite db + attachments) is declared in docker-compose.
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

# Apply migrations, then serve the API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
