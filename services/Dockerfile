FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/api/requirements.txt /app/services/api/requirements.txt
RUN pip install --no-cache-dir -r /app/services/api/requirements.txt

COPY scripts /app/scripts
COPY services /app/services
COPY data /app/data
COPY docs/company-knowledge-base /app/docs/company-knowledge-base

ENV PYTHONPATH=/app:/app/services/api
ENV UPLOAD_DIR=/data/uploads

RUN mkdir -p /data/uploads

EXPOSE 8001 5555
