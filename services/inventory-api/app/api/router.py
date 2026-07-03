from __future__ import annotations

from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routers.inventory import router as inventory_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(inventory_router)
