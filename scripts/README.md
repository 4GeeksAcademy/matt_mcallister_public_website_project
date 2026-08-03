## `seed_incidents.py`

Loads historical incidents from the analyzer CSV into the SQLite DB used by
`services/api`.

```bash
export INCIDENTS_DB_PATH="$(pwd)/data/process/incidents.db"
PYTHONPATH=. python3 scripts/seed_incidents.py \
  --csv-path data/raw/incidents-trackflow.csv
```

- Applies analyzer invalid-row rules, then CONTEXT transforms
- Forces `origin` to `customer`
- Maps `country` → `la_office` / `zaragoza_office`
- Idempotent on `incident_id`
