from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str
    sku: str
    warehouse_location: Literal["los_angeles", "zaragoza"]
    client_brand: str
    low_stock_threshold: int = Field(default=10, ge=0)


class ProductRead(BaseModel):
    id: int
    name: str
    sku: str
    warehouse_location: str
    client_brand: str
    low_stock_threshold: int
    current_stock: int


class InboundOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OutboundOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderRead(BaseModel):
    id: int
    order_type: Literal["inbound", "outbound"]
    product_id: int
    product_name: str
    product_sku: str
    quantity: int
    created_at: datetime
    user_uuid: str
