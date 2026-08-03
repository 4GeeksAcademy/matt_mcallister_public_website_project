# `data/pipelines` folder

This folder groups **all data pipelines in the monorepo** related to the company: ingestion, ETL/ELT, cleaning, transformation, and loading into analytical or production systems.

## Weekly Warehouse & Client Performance

| File | Role |
|------|------|
| [`PIPELINE_DESIGN.md`](./PIPELINE_DESIGN.md) | Design: KPIs, grain, idempotency, Prefect mapping |
| [`pipeline.py`](./pipeline.py) | Prefect ETL (extract / transform / load subflows) |
| [`reporting_store.py`](./reporting_store.py) | Destination upsert + query helpers (no Prefect) |
| [`requirements.txt`](./requirements.txt) | Prefect + pandas + pytest |

```bash
cd data/pipelines && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../..
WEEK_START=2026-07-06 python data/pipelines/pipeline.py
python -m pytest tests/pipelines/test_pipeline.py
```

Schedule: Mondays ~07:00 UTC (see design doc).

> _Spanish version: [README.es.md](./README.es.md)._
