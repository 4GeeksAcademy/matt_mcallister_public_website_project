from api.database import insert_many_suppliers
from api.models import SupplierCreate, utc_now
from api.seed_data import SUPPLIERS_SEED


def main() -> None:
    now = utc_now().isoformat()
    normalized = []

    for supplier in SUPPLIERS_SEED:
        validated = SupplierCreate.model_validate(supplier)
        normalized.append({**validated.model_dump(), "rate_updated_at": now})

    inserted = insert_many_suppliers(normalized)
    print(f"Seeder completed. Inserted {inserted} records.")


if __name__ == "__main__":
    main()
