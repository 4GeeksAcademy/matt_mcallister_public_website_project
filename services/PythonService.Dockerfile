FROM python:3.12-slim

ARG SERVICE_PATH

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r "/app/${SERVICE_PATH}/requirements.txt"

WORKDIR /app/${SERVICE_PATH}
ENV PYTHONPATH=/app:/app/${SERVICE_PATH}

EXPOSE 8000
