# Inventory API

FastAPI service for TrackFlow warehouse inventory. Uses TinyDB for user authentication and Supabase PostgreSQL (via SQLModel) for products and orders.

## Setup

```bash
cd services/inventory-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase DATABASE_URL and SECRET_KEY
```

## Run

```bash
uvicorn app.main:app --reload --port 3001
```

## Endpoints

- `POST /auth/register`, `POST /auth/login` — user authentication (TinyDB)
- `GET /users/me`, `PUT /users/{id}`, `PUT /users/{id}/change-password` — user profile
- `GET/POST /inventory/products` — product catalog with computed stock
- `POST /inventory/orders/inbound`, `POST /inventory/orders/outbound` — stock movements (auth required)
- `GET /inventory/orders` — all orders with product data
