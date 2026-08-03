"""In-memory inventory store with seed data for telemetry verification."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

Warehouse = Literal["los_angeles", "zaragoza"]
Category = Literal["fashion", "electronics", "cosmetics"]


@dataclass
class Product:
    product_id: str
    client_id: str
    name: str
    product_category: Category
    min_threshold: int


@dataclass
class StockKey:
    warehouse: Warehouse
    product_id: str


@dataclass
class InventoryState:
    products: dict[str, Product] = field(default_factory=dict)
    # key: f"{warehouse}:{product_id}" -> quantity
    stock: dict[str, int] = field(default_factory=dict)
    inbound_orders: list[dict] = field(default_factory=list)
    outbound_orders: list[dict] = field(default_factory=list)
    discrepancies: list[dict] = field(default_factory=list)


def _key(warehouse: str, product_id: str) -> str:
    return f"{warehouse}:{product_id}"


def build_seed_state() -> InventoryState:
    """8–10 SKUs, ≥2 clients, 3 categories, both warehouses."""
    products = [
        Product("SKU-F-001", "client_fashion_co", "T-Shirt Size M", "fashion", 20),
        Product("SKU-F-002", "client_fashion_co", "Denim Jacket", "fashion", 10),
        Product("SKU-F-003", "client_fashion_co", "Sneakers 42", "fashion", 15),
        Product("SKU-E-001", "client_electro_brand", "Bluetooth Headset", "electronics", 25),
        Product("SKU-E-002", "client_electro_brand", "USB-C Hub", "electronics", 30),
        Product("SKU-E-003", "client_electro_brand", "Wireless Mouse", "electronics", 20),
        Product("SKU-C-001", "client_fashion_co", "Lip Serum 30ml", "cosmetics", 40),
        Product("SKU-C-002", "client_electro_brand", "Face Cream SPF50", "cosmetics", 35),
        Product("SKU-C-003", "client_fashion_co", "Perfume 50ml", "cosmetics", 12),
    ]
    state = InventoryState(products={p.product_id: p for p in products})

    # Initial stock in both warehouses
    initial = {
        ("los_angeles", "SKU-F-001"): 80,
        ("los_angeles", "SKU-F-002"): 40,
        ("los_angeles", "SKU-F-003"): 55,
        ("los_angeles", "SKU-E-001"): 60,
        ("los_angeles", "SKU-E-002"): 70,
        ("los_angeles", "SKU-E-003"): 45,
        ("los_angeles", "SKU-C-001"): 90,
        ("los_angeles", "SKU-C-002"): 50,
        ("los_angeles", "SKU-C-003"): 25,
        ("zaragoza", "SKU-F-001"): 70,
        ("zaragoza", "SKU-F-002"): 35,
        ("zaragoza", "SKU-F-003"): 48,
        ("zaragoza", "SKU-E-001"): 55,
        ("zaragoza", "SKU-E-002"): 65,
        ("zaragoza", "SKU-E-003"): 40,
        ("zaragoza", "SKU-C-001"): 85,
        ("zaragoza", "SKU-C-002"): 45,
        ("zaragoza", "SKU-C-003"): 22,
    }
    for (wh, pid), qty in initial.items():
        state.stock[_key(wh, pid)] = qty

    # Seed historical inbound/outbound counts toward 15–20 each (in memory on first boot)
    # Remaining will be created via API during verification.
    return state


STATE = build_seed_state()


def list_products() -> list[dict]:
    return [
        {
            "product_id": p.product_id,
            "client_id": p.client_id,
            "name": p.name,
            "product_category": p.product_category,
            "min_threshold": p.min_threshold,
        }
        for p in STATE.products.values()
    ]


def list_stock() -> list[dict]:
    rows = []
    for key, qty in STATE.stock.items():
        warehouse, product_id = key.split(":", 1)
        product = STATE.products[product_id]
        rows.append(
            {
                "warehouse": warehouse,
                "product_id": product_id,
                "client_id": product.client_id,
                "product_category": product.product_category,
                "quantity": qty,
                "min_threshold": product.min_threshold,
            }
        )
    return rows


def create_inbound(
    warehouse: Warehouse,
    product_id: str,
    quantity: int,
) -> dict:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    product = STATE.products.get(product_id)
    if product is None:
        raise ValueError("unknown product_id")
    k = _key(warehouse, product_id)
    STATE.stock[k] = STATE.stock.get(k, 0) + quantity
    order = {
        "order_id": f"IN-{uuid4().hex[:8]}",
        "warehouse": warehouse,
        "client_id": product.client_id,
        "product_id": product_id,
        "product_category": product.product_category,
        "quantity": quantity,
    }
    STATE.inbound_orders.append(order)
    return order


def create_outbound(
    warehouse: Warehouse,
    product_id: str,
    quantity: int,
) -> dict:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    product = STATE.products.get(product_id)
    if product is None:
        raise ValueError("unknown product_id")
    k = _key(warehouse, product_id)
    current = STATE.stock.get(k, 0)
    if quantity > current:
        raise ValueError("insufficient stock")
    new_qty = current - quantity
    STATE.stock[k] = new_qty
    order = {
        "order_id": f"OUT-{uuid4().hex[:8]}",
        "warehouse": warehouse,
        "client_id": product.client_id,
        "product_id": product_id,
        "product_category": product.product_category,
        "quantity": quantity,
        "current_stock": new_qty,
        "min_threshold": product.min_threshold,
        "threshold_triggered": new_qty < product.min_threshold,
    }
    STATE.outbound_orders.append(order)
    return order


def reject_direct_edit(
    warehouse: Warehouse,
    product_id: str,
    attempted_delta: int,
) -> dict:
    product = STATE.products.get(product_id)
    if product is None:
        raise ValueError("unknown product_id")
    return {
        "warehouse": warehouse,
        "client_id": product.client_id,
        "product_id": product_id,
        "product_category": product.product_category,
        "quantity": STATE.stock.get(_key(warehouse, product_id), 0),
        "attempted_delta": attempted_delta,
        "reason": "stock_changes_must_go_through_orders",
        "rejected": True,
    }


def record_discrepancy(
    warehouse: Warehouse,
    product_id: str,
    counted_quantity: int,
) -> dict:
    product = STATE.products.get(product_id)
    if product is None:
        raise ValueError("unknown product_id")
    k = _key(warehouse, product_id)
    system_quantity = STATE.stock.get(k, 0)
    delta = counted_quantity - system_quantity
    row = {
        "warehouse": warehouse,
        "client_id": product.client_id,
        "product_id": product_id,
        "product_category": product.product_category,
        "quantity": abs(delta),
        "system_quantity": system_quantity,
        "counted_quantity": counted_quantity,
        "delta": delta,
    }
    STATE.discrepancies.append(row)
    # Align system to physical count after audit
    STATE.stock[k] = counted_quantity
    return row


def snapshot() -> dict:
    return {
        "products": list_products(),
        "stock": list_stock(),
        "inbound_count": len(STATE.inbound_orders),
        "outbound_count": len(STATE.outbound_orders),
        "discrepancy_count": len(STATE.discrepancies),
        "inbound_orders": deepcopy(STATE.inbound_orders),
        "outbound_orders": deepcopy(STATE.outbound_orders),
    }
