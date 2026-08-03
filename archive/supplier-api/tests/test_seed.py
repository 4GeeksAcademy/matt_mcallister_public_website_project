from app.db import insert_many_suppliers
from app.models import SupplierCreate, utc_now
from app.seed_data import SUPPLIERS_SEED


def test_seed_is_idempotent(isolated_db):
    now = utc_now().isoformat()
    normalized = []

    for supplier in SUPPLIERS_SEED:
        validated = SupplierCreate.model_validate(supplier)
        normalized.append({**validated.model_dump(), "rate_updated_at": now})

    first = insert_many_suppliers(normalized)
    second = insert_many_suppliers(normalized)

    assert first == 15
    assert second == 0
