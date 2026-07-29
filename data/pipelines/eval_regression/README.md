# TrackFlow regression evaluation pipeline

Predicts closed-incident `satisfaction_score` (1–5) from TrackFlow domain features using temporal cross-validation.

## Setup

```bash
cd data/pipelines/eval_regression
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate training data

```bash
python generate_data.py
# writes ../../raw/incidents_train.csv
```

## Run evaluation

```bash
python run_eval.py
```

Artifacts written to `data/eval/`:

- `learning_curve.png`
- `cv_metrics.json`

## Tests

From repo root (with the venv active and `PYTHONPATH` set to this directory):

```bash
cd <repo-root>
PYTHONPATH=data/pipelines/eval_regression pytest tests/pipelines/ -q
```
