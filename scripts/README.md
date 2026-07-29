# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

## TrackFlow sales regression

```bash
# from repo root, with sklearn/pandas/matplotlib available
python scripts/generate_trackflow_sales.py   # writes data/raw/trackflow_sales.csv
python scripts/train_sales_model.py          # model + metrics + plot under data/eval/
PYTHONPATH=scripts pytest tests/pipelines/test_sales_train_test_split.py -q
```

Context: [`CONTEXT-sales-prediction.md`](../CONTEXT-sales-prediction.md).

> _Spanish version: [README.es.md](./README.es.md)._
