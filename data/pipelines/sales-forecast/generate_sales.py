"""Generate synthetic TrackFlow monthly sales CSV (seeded, CONTEXT-aligned)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
START_YEAR = 2016
END_YEAR = 2025

# country, warehouse, service_line, base_monthly_revenue_eur (2016 level)
SLICES = [
    ("US", "Los_Angeles", "fulfillment", 125_000.0),
    ("US", "Los_Angeles", "last_mile", 68_000.0),
    ("US", "Los_Angeles", "returns", 32_000.0),
    ("ES", "Zaragoza", "fulfillment", 68_000.0),
    ("ES", "Zaragoza", "last_mile", 40_000.0),
    ("ES", "Zaragoza", "returns", 20_000.0),
]


def _seasonal_factor(month: int, country: str) -> float:
    """Q4 peak; US Nov Black Friday; ES summer soft + Dec Christmas."""
    base = {
        1: 0.85,
        2: 0.88,
        3: 0.95,
        4: 0.98,
        5: 1.00,
        6: 0.97,
        7: 0.94,
        8: 0.93,
        9: 1.02,
        10: 1.12,
        11: 1.25,
        12: 1.35,
    }[month]
    if country == "US" and month == 11:
        return base * 1.08
    if country == "ES":
        if month in (7, 8):
            return base * 0.90
        if month == 12:
            return base * 1.05
    return base


def _growth_factor(year: int) -> float:
    """Gradual climb so recent years approach ~€9M ARR."""
    # years from 2016: 0..9 → ~1.0 .. ~2.05
    t = year - START_YEAR
    return 1.0 + 0.09 * t + 0.0025 * (t**2)


def generate_sales(seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []

    for year in range(START_YEAR, END_YEAR + 1):
        g = _growth_factor(year)
        for month in range(1, 13):
            for country, warehouse, service_line, base_rev in SLICES:
                season = _seasonal_factor(month, country)
                noise = float(rng.normal(1.0, 0.035))
                revenue = base_rev * g * season * noise
                avg_order_value = 42.0 if country == "US" else 38.0
                if service_line == "returns":
                    avg_order_value *= 0.7
                orders = max(1, int(round(revenue / avg_order_value)))
                returns_rate = float(rng.uniform(0.18, 0.25))
                rows.append(
                    {
                        "date": f"{year:04d}-{month:02d}-01",
                        "year": year,
                        "month": month,
                        "country": country,
                        "warehouse": warehouse,
                        "service_line": service_line,
                        "orders": orders,
                        "revenue_eur": round(revenue, 2),
                        "returns_rate": round(returns_rate, 4),
                    }
                )

    return pd.DataFrame(rows)


def main() -> None:
    out = Path(__file__).resolve().parents[2] / "raw" / "trackflow_sales.csv"
    df = generate_sales()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    annual = df.groupby("year")["revenue_eur"].sum()
    print(f"Wrote {len(df)} rows → {out}")
    print("Annual revenue_eur by year:")
    print(annual.round(0).astype(int).to_string())


if __name__ == "__main__":
    main()
