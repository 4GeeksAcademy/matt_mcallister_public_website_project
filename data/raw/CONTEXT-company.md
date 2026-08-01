# TrackFlow — Sales Dataset Context

Company-specific schema and generation rules for the historical sales series used in sales forecasting.

**Source file:** `data/raw/trackflow_sales.csv`  
**Company briefing:** see root [`CONTEXT.md`](../../CONTEXT.md)

## Business anchors (from CONTEXT.md)

| Fact | Value |
|------|--------|
| Founded | 2009 (Los Angeles) |
| Markets | United States (`US`), Spain (`ES`) |
| Warehouses | Los Angeles (`Los_Angeles`), Zaragoza (`Zaragoza`) |
| Approx. annual revenue | ~€9M in recent years |
| Returns volume | 18–25% of total volume (by client/country) |
| Service lines | Fulfillment / warehouse ops, last-mile delivery, reverse logistics (returns) |

## Dataset schema (monthly grain)

One row = one month × country × warehouse × service line.

| Column | Type | Allowed values / notes |
|--------|------|------------------------|
| `date` | ISO date (`YYYY-MM-01`) | First day of the month |
| `year` | int | Calendar year |
| `month` | int | 1–12 |
| `country` | string | `US` or `ES` |
| `warehouse` | string | `Los_Angeles` (US) or `Zaragoza` (ES) |
| `service_line` | string | `fulfillment`, `last_mile`, or `returns` |
| `orders` | int | Order / shipment volume for that slice |
| `revenue_eur` | float | Revenue in euros |
| `returns_rate` | float | Fraction in **[0.18, 0.25]** |

## Coverage

- **Window:** 2016-01 through 2025-12 (10 calendar years of monthly data)
- **Train / test rule:** first **8** years for training, last **2** years for testing — no date overlap, no shuffle across the cut

## Growth pattern (do not break)

- Gradual climb in total annual revenue toward ~€9M ARR in the most recent years
- US volume is larger than ES overall; both markets grow over time
- Do **not** flatten the series or replace it with IID noise that removes the growth trend

## Seasonality pattern (do not break)

- **Q4 e-commerce peak** (especially October–December) for both markets
- **US:** Thanksgiving / Black Friday lift in November; strong December
- **ES:** summer soft patch mid-year; Christmas peak in December
- Returns-related `returns_rate` stays inside the 18–25% band from CONTEXT.md

## Alteration rule

Do **not** alter `trackflow_sales.csv` in ways that destroy the growth trend or seasonal peaks described above. Column names and formats must match this document.
