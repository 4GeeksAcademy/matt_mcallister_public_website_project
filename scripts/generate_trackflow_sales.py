"""Generate TrackFlow monthly consolidated sales CSV (deterministic, seed=42)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "trackflow_sales.csv"

X = 0.06
Y = 0.03
RANDOM_STATE = 42
BASE_MONTHLY_EUR = 520_000.0


def generate_trackflow_sales(random_state: int = RANDOM_STATE) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    rows: list[dict] = []
    annual_level = BASE_MONTHLY_EUR

    for year_index, year in enumerate(range(2016, 2026)):
        if year_index > 0:
            d = (X + Y) if year_index % 2 == 1 else (X - Y)
            annual_level = annual_level * (1.0 + d)

        for month in range(1, 13):
            if month in (11, 12):
                factor = 1.0 + float(rng.uniform(0.25, 0.35))
            elif month == 2:
                factor = 1.0 - float(rng.uniform(0.10, 0.15))
            else:
                factor = 1.0 + float(rng.uniform(-0.05, 0.05))

            revenue = float(annual_level * factor)
            arps = float(rng.uniform(18.0, 28.0))
            shipments = int(max(1, round(revenue / arps)))
            arps = revenue / shipments

            rows.append(
                {
                    "month": f"{year:04d}-{month:02d}-01",
                    "revenue_eur": round(revenue, 2),
                    "shipments_processed": shipments,
                    "avg_revenue_per_shipment_eur": round(arps, 4),
                    "market": "consolidated",
                }
            )

    df = pd.DataFrame(rows)
    assert len(df) == 120
    assert (df["revenue_eur"] > 0).all()
    assert df["market"].eq("consolidated").all()
    # No missing months
    expected = pd.date_range("2016-01-01", "2025-12-01", freq="MS")
    assert list(pd.to_datetime(df["month"])) == list(expected)
    return df


def main() -> None:
    df = generate_trackflow_sales()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
