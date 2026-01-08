ARG PYTHON_VERSION=python:3.11-slim

FROM ${PYTHON_VERSION} AS builder

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        libpq-dev \
        gcc \
        pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

WORKDIR /app

COPY requirements.txt ./

# ⭐ สำคัญ: แก้ไข setuptools และ pip ก่อน
RUN /venv/bin/pip install --upgrade pip setuptools==68.0.0 wheel \
    && /venv/bin/pip install -r requirements.txt

FROM ${PYTHON_VERSION}

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libpq5 \
        curl \
        netcat-traditional \
        procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
ENV PATH=/venv/bin:$PATH

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SETUPTOOLS_USE_DISTUTILS=stdlib

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

COPY . /app

RUN mkdir -p /app/logs

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "\
    echo '🔄 Waiting for database...' && \
    while ! nc -z db 5432; do \
        echo '⏳ Database not ready, waiting...'; \
        sleep 2; \
    done && \
    echo '✅ Database is ready!' && \
    echo '🏗️ Initializing database...' && \
    python create_tables.py docker-init && \
    echo '🚀 Starting FastAPI server...' && \
    cd app && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]