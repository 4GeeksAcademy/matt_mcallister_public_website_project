from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select
from typing import List, Optional

from app.models.inventory import InboundOrder, OutboundOrder, Product
from app.schemas.inventory import (
    InboundOrderCreate,
    OrderRead,
    OutboundOrderCreate,
    ProductCreate,
    ProductRead,
)


def compute_current_stock(session: Session, product_id: int) -> int:
    inbound_total = session.exec(
        select(func.coalesce(func.sum(InboundOrder.quantity), 0)).where(
            InboundOrder.product_id == product_id
        )
    ).one()
    outbound_total = session.exec(
        select(func.coalesce(func.sum(OutboundOrder.quantity), 0)).where(
            OutboundOrder.product_id == product_id
        )
    ).one()
    return int(inbound_total) - int(outbound_total)


def product_to_read(session: Session, product: Product) -> ProductRead:
    return ProductRead(
        id=product.id,
        name=product.name,
        sku=product.sku,
        warehouse_location=product.warehouse_location,
        client_brand=product.client_brand,
        low_stock_threshold=product.low_stock_threshold,
        current_stock=compute_current_stock(session, product.id),
    )


def list_products(session: Session) -> List[ProductRead]:
    products = session.exec(select(Product).order_by(Product.id)).all()
    return [product_to_read(session, product) for product in products]


def get_product(session: Session, product_id: int) -> Optional[Product]:
    return session.get(Product, product_id)


def get_product_read(session: Session, product_id: int) -> Optional[ProductRead]:
    product = get_product(session, product_id)
    if product is None:
        return None
    return product_to_read(session, product)


def create_product(session: Session, payload: ProductCreate) -> ProductRead:
    existing = session.exec(select(Product).where(Product.sku == payload.sku)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{payload.sku}' already exists",
        )

    product = Product.model_validate(payload)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product_to_read(session, product)


def create_inbound_order(
    session: Session, payload: InboundOrderCreate, user_uuid: str
) -> InboundOrder:
    product = get_product(session, payload.product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {payload.product_id} not found",
        )

    order = InboundOrder(
        product_id=payload.product_id,
        quantity=payload.quantity,
        user_uuid=user_uuid,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def create_outbound_order(
    session: Session, payload: OutboundOrderCreate, user_uuid: str
) -> OutboundOrder:
    product = get_product(session, payload.product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {payload.product_id} not found",
        )

    current_stock = compute_current_stock(session, payload.product_id)
    if current_stock - payload.quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient stock for SKU '{product.sku}'. "
                f"Current stock: {current_stock}, requested: {payload.quantity}"
            ),
        )

    order = OutboundOrder(
        product_id=payload.product_id,
        quantity=payload.quantity,
        user_uuid=user_uuid,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def list_orders(session: Session) -> List[OrderRead]:
    inbound_orders = session.exec(
        select(InboundOrder, Product)
        .join(Product, InboundOrder.product_id == Product.id)
        .order_by(InboundOrder.created_at.desc())
    ).all()
    outbound_orders = session.exec(
        select(OutboundOrder, Product)
        .join(Product, OutboundOrder.product_id == Product.id)
        .order_by(OutboundOrder.created_at.desc())
    ).all()

    orders: List[OrderRead] = []
    for order, product in inbound_orders:
        orders.append(
            OrderRead(
                id=order.id,
                order_type="inbound",
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=order.quantity,
                created_at=order.created_at,
                user_uuid=order.user_uuid,
            )
        )
    for order, product in outbound_orders:
        orders.append(
            OrderRead(
                id=order.id,
                order_type="outbound",
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=order.quantity,
                created_at=order.created_at,
                user_uuid=order.user_uuid,
            )
        )

    orders.sort(key=lambda item: item.created_at, reverse=True)
    return orders
