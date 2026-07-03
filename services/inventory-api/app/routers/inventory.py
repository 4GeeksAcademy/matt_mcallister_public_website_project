from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.inventory import (
    InboundOrderCreate,
    OrderRead,
    OutboundOrderCreate,
    ProductCreate,
    ProductRead,
)
from app.services import inventory_service


router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/products", response_model=list[ProductRead])
def list_products(session: Session = Depends(get_db)) -> list[ProductRead]:
    return inventory_service.list_products(session)


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductRead:
    _ = current_user
    return inventory_service.create_product(session, payload)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_db)) -> ProductRead:
    product = inventory_service.get_product_read(session, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    return product


@router.post("/orders/inbound", status_code=status.HTTP_201_CREATED)
def create_inbound_order(
    payload: InboundOrderCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    order = inventory_service.create_inbound_order(
        session, payload, user_uuid=str(current_user.id)
    )
    return {"id": order.id, "product_id": order.product_id, "quantity": order.quantity}


@router.post("/orders/outbound", status_code=status.HTTP_201_CREATED)
def create_outbound_order(
    payload: OutboundOrderCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    order = inventory_service.create_outbound_order(
        session, payload, user_uuid=str(current_user.id)
    )
    return {"id": order.id, "product_id": order.product_id, "quantity": order.quantity}


@router.get("/orders", response_model=list[OrderRead])
def list_orders(session: Session = Depends(get_db)) -> list[OrderRead]:
    return inventory_service.list_orders(session)
