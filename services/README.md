# `services` folder

TrackFlow backend services. The incidents API lives under `services/api`.

```bash
cd services/api
pip install -r requirements.txt
INCIDENTS_DB_PATH=../../data/process/incidents.db \
PYTHONPATH=../.. \
uvicorn app.main:app --host 0.0.0.0 --port 8001
```
