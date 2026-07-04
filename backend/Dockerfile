# AQAA backend -- FastAPI + SQLAlchemy (async) + document-processing toolchain.
#
# Build:
#   docker build -t aqaa-backend ./backend
#
# Run (standalone, expects an external Postgres reachable via DATABASE_URL):
#   docker run --rm -p 8000:8000 --env-file ./backend/.env aqaa-backend
#
# Normally run via the root docker-compose.yml, which wires this image up to
# the postgres / redis / qdrant services.

FROM python:3.13-slim

# --- OS-level dependencies ---
# tesseract-ocr      : required at runtime by pytesseract (OCR for scanned
#                       evidence documents -- Module Folder Audit Agent).
# libgl1, libglib2.0 : transitive runtime deps for Pillow/image handling.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python dependencies (cached separately from app code) ---
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Application code ---
COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
