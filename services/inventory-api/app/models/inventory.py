from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(unique=True, index=True)
    warehouse_location: str
    client_brand: str
    low_stock_threshold: int = Field(default=10)


class InboundOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_uuid: str


class OutboundOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_uuid: str
