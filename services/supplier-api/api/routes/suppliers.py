from fastapi import APIRouter, HTTPException, Query, status

from api.constants import VALID_CATEGORIES, VALID_COUNTRIES
from api.database import (
    create_supplier,
    delete_supplier,
    find_supplier,
    list_suppliers,
    serialize_supplier,
    update_supplier,
)
from api.models import (
    RateUpdateRequest,
    StatusUpdateRequest,
    SupplierCreate,
    SupplierResponse,
    utc_now,
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier_endpoint(payload: SupplierCreate) -> SupplierResponse:
    now = utc_now().isoformat()
    created = create_supplier({**payload.model_dump(), "rate_updated_at": now})
    return SupplierResponse.model_validate(created)


@router.get("", response_model=list[SupplierResponse])
def list_suppliers_endpoint(
    country: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> list[SupplierResponse]:
    if country is not None and country not in VALID_COUNTRIES:
        raise HTTPException(status_code=422, detail="invalid country filter")
    if category is not None and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="invalid category filter")

    suppliers = list_suppliers(country=country, category=category)
    return [SupplierResponse.model_validate(item) for item in suppliers]


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier_endpoint(supplier_id: int) -> SupplierResponse:
    supplier = find_supplier(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="supplier not found")
    return SupplierResponse.model_validate(serialize_supplier(supplier))


@router.patch("/{supplier_id}/rate", response_model=SupplierResponse)
def patch_supplier_rate_endpoint(
    supplier_id: int,
    payload: RateUpdateRequest,
) -> SupplierResponse:
    updates = {
        "rate_per_shipment": payload.rate_per_shipment,
        "rate_updated_at": utc_now().isoformat(),
    }
    updated = update_supplier(supplier_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="supplier not found")
    return SupplierResponse.model_validate(updated)


@router.patch("/{supplier_id}/status", response_model=SupplierResponse)
def patch_supplier_status_endpoint(
    supplier_id: int,
    payload: StatusUpdateRequest,
) -> SupplierResponse:
    updated = update_supplier(supplier_id, {"status": payload.status.value})
    if updated is None:
        raise HTTPException(status_code=404, detail="supplier not found")
    return SupplierResponse.model_validate(updated)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier_endpoint(supplier_id: int) -> None:
    deleted = delete_supplier(supplier_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="supplier not found")
