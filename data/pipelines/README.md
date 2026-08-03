# `data/pipelines` folder

This folder groups **all data pipelines in the monorepo** related to the company: ingestion, ETL/ELT, cleaning, transformation, and loading into analytical or production systems.

## TrackFlow warehouse telemetry ETL

| File | Role |
|------|------|
| [`PIPELINE_DESIGN.md`](./PIPELINE_DESIGN.md) | Design: current state, flow, idempotency, Prefect mapping |
| [`pipeline.py`](./pipeline.py) | Prefect main flow + subflows + tasks (CLI entrypoint) |
| [`requirements.txt`](./requirements.txt) | Python deps (`prefect`, `pandas`, …) |
| [`telemetry-stream/`](./telemetry-stream/) | Event JSON Schema + sample envelope |

**Run:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r data/pipelines/requirements.txt
python data/pipelines/pipeline.py
```

**Tests:**

```bash
python -m pytest tests/pipelines/test_pipeline.py
```

> _Spanish version: [README.es.md](./README.es.md)._
