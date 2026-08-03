import os
from datetime import datetime
from pathlib import Path

from tinydb import Query, TinyDB
from tinydb.table import Document

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "suppliers.json"


def get_db_path() -> Path:
    configured = os.environ.get("SUPPLIERS_DB_PATH")
    if configured:
        return Path(configured)
    return DEFAULT_DB_PATH


def get_db() -> TinyDB:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(db_path)


def suppliers_table():
    return get_db().table("suppliers")


def serialize_supplier(doc: Document) -> dict:
    payload = dict(doc)
    payload["id"] = doc.doc_id
    payload["rate_updated_at"] = datetime.fromisoformat(payload["rate_updated_at"])
    return payload


def find_supplier(doc_id: int) -> Document | None:
    return suppliers_table().get(doc_id=doc_id)


def list_suppliers(country: str | None = None, category: str | None = None) -> list[dict]:
    table = suppliers_table()
    supplier = Query()
    docs = table.all()

    if country:
        docs = [doc for doc in docs if doc.get("country") == country]

    if category:
        docs = [doc for doc in docs if category in doc.get("categories", [])]

    return [serialize_supplier(doc) for doc in docs]


def create_supplier(payload: dict) -> dict:
    table = suppliers_table()
    doc_id = table.insert(payload)
    created = table.get(doc_id=doc_id)
    if created is None:
        raise RuntimeError("failed to load inserted supplier")
    return serialize_supplier(Document(created, doc_id=doc_id))


def update_supplier(doc_id: int, updates: dict) -> dict | None:
    table = suppliers_table()
    updated_count = table.update(updates, doc_ids=[doc_id])
    if not updated_count:
        return None
    current = table.get(doc_id=doc_id)
    if current is None:
        return None
    return serialize_supplier(Document(current, doc_id=doc_id))


def delete_supplier(doc_id: int) -> bool:
    table = suppliers_table()
    if table.get(doc_id=doc_id) is None:
        return False

    deleted = table.remove(doc_ids=[doc_id])
    return bool(deleted)


def supplier_exists_by_name_country(name: str, country: str) -> bool:
    supplier = Query()
    return suppliers_table().contains((supplier.name == name) & (supplier.country == country))


def insert_many_suppliers(suppliers: list[dict]) -> int:
    table = suppliers_table()
    inserted = 0
    for supplier in suppliers:
        if supplier_exists_by_name_country(supplier["name"], supplier["country"]):
            continue
        table.insert(supplier)
        inserted += 1
    return inserted
