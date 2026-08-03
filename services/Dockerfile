FROM python:3.12-slim

WORKDIR /app

COPY inventory-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY inventory-api/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
