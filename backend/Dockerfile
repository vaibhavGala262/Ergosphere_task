FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_DEFAULT_TIMEOUT=300

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --retries 10 --timeout 300 --index-url https://download.pytorch.org/whl/cpu torch==2.5.1+cpu && \
    pip install --no-cache-dir --retries 10 --timeout 300 -r /app/requirements.txt

COPY backend /app/backend
RUN dos2unix /app/backend/entrypoint.sh && chmod +x /app/backend/entrypoint.sh

WORKDIR /app/backend
EXPOSE 8000
