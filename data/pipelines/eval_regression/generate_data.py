"""Generate a reproducible chronological TrackFlow incidents training CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from domain import (
    CARRIERS_BY_COUNTRY,
    CUSTOMER_TYPES,
    VALID_CATEGORIES,
    VALID_COUNTRIES,
)

# Category base CSAT (1–5); lower = worse typical outcome for TrackFlow ops.
CATEGORY_BASE = {
    "LOST_PARCEL": 1.8,
    "DAMAGE": 2.2,
    "WRONG_ADDRESS": 2.6,
    "DELAYED_DELIVERY": 3.0,
    "RETURN_REQUEST": 3.4,
}
CARRIER_OFFSET = {
    "UPS": 0.2,
    "FEDEX": 0.1,
    "DHL_US": 0.0,
    "MRW": 0.15,
    "SEUR": 0.05,
    "DHL_ES": -0.05,
    "LOCAL_ES": -0.15,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def generate_incidents(n_rows: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2023-01-01")
    # One incident per day-ish with slight jitter so dates are strictly ordered.
    dates = pd.date_range(start, periods=n_rows, freq="D")

    rows: list[dict] = []
    for i, date in enumerate(dates):
        country = VALID_COUNTRIES[int(rng.integers(0, len(VALID_COUNTRIES)))]
        carriers = CARRIERS_BY_COUNTRY[country]
        carrier = carriers[int(rng.integers(0, len(carriers)))]
        category = VALID_CATEGORIES[int(rng.integers(0, len(VALID_CATEGORIES)))]
        customer_type = CUSTOMER_TYPES[int(rng.integers(0, len(CUSTOMER_TYPES)))]

        # Mild temporal drift: CSAT improves slowly over the series.
        time_boost = 0.4 * (i / max(n_rows - 1, 1))
        b2b_boost = 0.25 if customer_type == "B2B" else 0.0
        mean = (
            CATEGORY_BASE[category]
            + CARRIER_OFFSET[carrier]
            + time_boost
            + b2b_boost
        )
        score = int(np.clip(np.round(rng.normal(mean, 0.55)), 1, 5))

        rows.append(
            {
                "incident_id": f"TRF-{i + 1:06d}",
                "date": date.strftime("%Y-%m-%d"),
                "country": country,
                "customer_type": customer_type,
                "tracking_number": f"TRACK{i + 1:08d}",
                "carrier": carrier,
                "category": category,
                "description": f"Closed {category} incident handled for {carrier}",
                "status": "CLOSED",
                "customer_email": f"client{i + 1}@example.com",
                "satisfaction_score": score,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TrackFlow incidents training CSV")
    parser.add_argument("--n-rows", type=int, default=800)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=_repo_root() / "data" / "raw" / "incidents_train.csv",
    )
    args = parser.parse_args()

    df = generate_incidents(n_rows=args.n_rows, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df)} rows to {args.output}")


if __name__ == "__main__":
    main()
