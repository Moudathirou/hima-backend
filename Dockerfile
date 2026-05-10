FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    DATABASE_URL="sqlite:////data/hima.db"

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

COPY . .

RUN useradd -m -u 1000 appuser \
 && mkdir -p /data \
 && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

VOLUME ["/data"]

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
