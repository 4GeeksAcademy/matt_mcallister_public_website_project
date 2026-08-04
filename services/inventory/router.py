"""Inventory API — thin stubs for telemetry instrumentation."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from inventory import store

router = APIRouter(prefix="/inventory", tags=["inventory"])

Warehouse = Literal["los_angeles", "zaragoza"]


class OrderRequest(BaseModel):
    warehouse: Warehouse
    product_id: str
    quantity: int = Field(..., gt=0)


class DirectEditRequest(BaseModel):
    warehouse: Warehouse
    product_id: str
    attempted_delta: int


class DiscrepancyRequest(BaseModel):
    warehouse: Warehouse
    product_id: str
    counted_quantity: int = Field(..., ge=0)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/products")
def get_products() -> list[dict]:
    return store.list_products()


@router.get("/stock")
def get_stock() -> list[dict]:
    return store.list_stock()


@router.get("/snapshot")
def get_snapshot() -> dict:
    return store.snapshot()


@router.post("/inbound")
def post_inbound(body: OrderRequest) -> dict:
    try:
        return store.create_inbound(body.warehouse, body.product_id, body.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/outbound")
def post_outbound(body: OrderRequest) -> dict:
    try:
        return store.create_outbound(body.warehouse, body.product_id, body.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/stock/direct-edit")
def post_direct_edit(body: DirectEditRequest) -> dict:
    """Always rejects — stock changes must go through orders."""
    try:
        return store.reject_direct_edit(
            body.warehouse, body.product_id, body.attempted_delta
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/discrepancy")
def post_discrepancy(body: DiscrepancyRequest) -> dict:
    try:
        return store.record_discrepancy(
            body.warehouse, body.product_id, body.counted_quantity
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/login")
def login(body: LoginRequest) -> dict:
    """Demo auth: password must be 'trackflow'."""
    if body.password != "trackflow":
        return {"ok": False, "failure_code": "invalid_credentials"}
    return {
        "ok": True,
        "userId": f"user_{body.username}",
        "sessionId": f"sess_{body.username}_{body.username[::-1]}",
    }
