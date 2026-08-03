from api.seed_data import SUPPLIERS_SEED


def valid_payload() -> dict:
    return {
        "name": "Carrier Nova",
        "country": "USA",
        "categories": ["carrier_last_mile"],
        "rate_per_shipment": 8.75,
        "currency": "USD",
        "status": "active",
        "service_zone": "West Coast",
        "contact_email": "ops@carriernova.com",
        "notes": "Pilot provider",
    }


def test_create_supplier_and_get_by_id(client):
    response = client.post("/suppliers", json=valid_payload())
    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 0
    assert created["rate_updated_at"]

    detail = client.get(f"/suppliers/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "Carrier Nova"


def test_create_supplier_invalid_currency_country_pair_returns_422(client):
    payload = valid_payload()
    payload["currency"] = "EUR"
    response = client.post("/suppliers", json=payload)
    assert response.status_code == 422


def test_list_suppliers_with_filters(client):
    client.post("/suppliers", json=valid_payload())

    payload = valid_payload()
    payload["name"] = "Iberia Logistics"
    payload["country"] = "Spain"
    payload["currency"] = "EUR"
    payload["categories"] = ["reverse_logistics"]
    client.post("/suppliers", json=payload)

    by_country = client.get("/suppliers", params={"country": "Spain"})
    assert by_country.status_code == 200
    assert len(by_country.json()) == 1

    by_category = client.get("/suppliers", params={"category": "carrier_last_mile"})
    assert by_category.status_code == 200
    assert len(by_category.json()) == 1

    invalid_country = client.get("/suppliers", params={"country": "France"})
    assert invalid_country.status_code == 422


def test_patch_rate_updates_timestamp_and_rejects_non_positive(client):
    created = client.post("/suppliers", json=valid_payload()).json()

    first_timestamp = created["rate_updated_at"]
    response = client.patch(
        f"/suppliers/{created['id']}/rate",
        json={"rate_per_shipment": 9.10},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["rate_per_shipment"] == 9.10
    assert updated["rate_updated_at"] != first_timestamp

    invalid = client.patch(
        f"/suppliers/{created['id']}/rate",
        json={"rate_per_shipment": 0},
    )
    assert invalid.status_code == 422


def test_patch_status_and_delete(client):
    created = client.post("/suppliers", json=valid_payload()).json()

    suspended = client.patch(
        f"/suppliers/{created['id']}/status",
        json={"status": "suspended"},
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"

    invalid_status = client.patch(
        f"/suppliers/{created['id']}/status",
        json={"status": "paused"},
    )
    assert invalid_status.status_code == 422

    deleted = client.delete(f"/suppliers/{created['id']}")
    assert deleted.status_code == 204

    missing = client.get(f"/suppliers/{created['id']}")
    assert missing.status_code == 404


def test_seed_data_exact_count_is_15():
    assert len(SUPPLIERS_SEED) == 15
