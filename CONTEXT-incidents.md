# CONTEXT — TrackFlow Centralized Incident Manager

## Company
TrackFlow — last-mile delivery and warehouse management (Los Angeles + Zaragoza).

## Incident model

| Field | Required | Notes |
|---|---|---|
| `id` | auto | Unique identifier |
| `title` | yes | Short title |
| `description` | yes | Detailed description |
| `category` | yes | See allowed values |
| `status` | yes | Lifecycle state |
| `origin` | yes | Who reported |
| `branch` | yes | Always required; use `central` when not branch-specific |
| `created_at` | auto | Creation timestamp (ISO-8601) |
| `updated_at` | auto | Last update timestamp |

### Allowed values

- **status:** `open`, `in_progress`, `resolved`, `discarded`
- **origin:** `customer`, `branch`, `internal`
- **category:** `lost_parcel`, `failed_delivery`, `wrong_address`, `inventory_discrepancy`
- **branch:** `Los Angeles`, `Zaragoza`, `central`

### Lifecycle

- `open` → `in_progress` \| `discarded`
- `in_progress` → `resolved` \| `discarded`
- `resolved` / `discarded` → (final; no further transitions)

---

## Historical CSV seed

**Source file:** `data/raw/incidents_history.csv`

Every seeded row must set `origin` to `"customer"`.

### Column transforms (CSV → model)

| CSV column | Model field |
|---|---|
| `description` | `title` (and also stored as `description`) |
| `date` | `created_at` (parsed as UTC midnight ISO) |
| `location` | `branch` (via location map) |
| `status` | `status` (via status map) |
| `category` | `category` (via category map) |
| `incident_id` | idempotency key (`seed_key`) |

### Status map

| CSV | Model |
|---|---|
| `OPEN` | `open` |
| `IN_PROGRESS` | `in_progress` |
| `CLOSED` / `RESOLVED` | `resolved` |
| `DISCARDED` | `discarded` |

### Category map

| CSV | Model |
|---|---|
| `LOST_PARCEL` | `lost_parcel` |
| `DELAYED_DELIVERY` / `FAILED_DELIVERY` / `DAMAGE` | `failed_delivery` |
| `WRONG_ADDRESS` | `wrong_address` |
| `INVENTORY_DISCREPANCY` / `RETURN_REQUEST` | `inventory_discrepancy` |

### Location / branch map

| CSV `location` | Model `branch` |
|---|---|
| `US`, `Los Angeles`, … | `Los Angeles` |
| `ES`, `Zaragoza`, … | `Zaragoza` |
| `central`, `CENTRAL`, `HQ` | `central` |

Unmapped locations are **invalid** and must not be inserted.

Invalid CSV rows must not be inserted and must be reported on the console.

---

## Expected summary after seeding `incidents_history.csv`

Valid rows inserted: **10** (plus **3** invalid CSV rows reported — empty description, unknown category, unmapped location — and not inserted).

All seeded incidents have `origin: customer`.

| Dimension | Expected counts |
|---|---|
| **by_status** | `open`: 4, `in_progress`: 1, `resolved`: 3, `discarded`: 2 |
| **by_category** | `lost_parcel`: 3, `failed_delivery`: 3, `wrong_address`: 2, `inventory_discrepancy`: 2 |
| **by_origin** | `customer`: 10, `branch`: 0, `internal`: 0 |
| **by_branch** | `Los Angeles`: 5, `Zaragoza`: 4, `central`: 1 |

Re-running the seed must not duplicate rows (idempotent on `incident_id`).
