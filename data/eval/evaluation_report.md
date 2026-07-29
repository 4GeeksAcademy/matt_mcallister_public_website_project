# TrackFlow Regression Evaluation Report

**Model:** One-hot encoding of TrackFlow incident fields + Ridge (`alpha=1.0`)  
**Target:** `satisfaction_score` (1–5) on closed incidents  
**Data:** [`data/raw/incidents_train.csv`](../raw/incidents_train.csv) (800 chronological rows; IDs `TRF-*`)  
**Artifacts:** [`learning_curve.png`](./learning_curve.png), [`cv_metrics.json`](./cv_metrics.json)

## Domain features (CONTEXT.md)

| Field | Values used |
|-------|-------------|
| `country` | `US`, `ES` |
| `customer_type` | `B2B`, `B2C` |
| `carrier` | US: `UPS`, `FEDEX`, `DHL_US`; ES: `MRW`, `SEUR`, `DHL_ES`, `LOCAL_ES` |
| `category` | `LOST_PARCEL`, `DELAYED_DELIVERY`, `WRONG_ADDRESS`, `RETURN_REQUEST`, `DAMAGE` |
| Calendar | `month`, `day_of_week` derived from `date` |

Carriers are always consistent with country, matching Last Mile operations in Los Angeles and Zaragoza.

## Temporal cross-validation

Strategy: `sklearn.model_selection.TimeSeriesSplit(n_splits=5)` with **no shuffle**.  
Each fold was checked so that `max(train_idx) < min(test_idx)` and indices within each side are strictly increasing (chronological order preserved).

| Fold | n_train | n_val | Train MAE | Train RMSE | Val MAE | Val RMSE |
|------|---------|-------|-----------|------------|---------|----------|
| 0 | 135 | 133 | 0.429 | 0.537 | 0.656 | 0.808 |
| 1 | 268 | 133 | 0.477 | 0.610 | 0.523 | 0.659 |
| 2 | 401 | 133 | 0.493 | 0.624 | 0.505 | 0.618 |
| 3 | 534 | 133 | 0.493 | 0.620 | 0.579 | 0.710 |
| 4 | 667 | 133 | 0.509 | 0.636 | 0.592 | 0.722 |

**Primary metric (validation MAE):** **0.5710 ± 0.0601** (mean ± std across 5 folds)

**Validation RMSE:** 0.7033 ± 0.0716

**Training MAE:** 0.4801 ± 0.0305  
**Training RMSE:** 0.6056 ± 0.0394

## Metric selection and business cost

Both MAE and RMSE were computed on train and validation for every fold.

**Primary metric: MAE.** Per [`CONTEXT-company.md`](../../CONTEXT-company.md), TrackFlow renewals and CX steering depend on *typical* CSAT accuracy on closed incidents. An average absolute miss of ~0.57 points on a 1–5 score misstates how healthy ops feel to B2B brands and B2C recipients. RMSE (0.70) remains a secondary check for outlier-heavy categories such as `LOST_PARCEL` and `DAMAGE`, but day-to-day reporting cost is better captured by MAE.

## Learning curve

See [`learning_curve.png`](./learning_curve.png). Training and validation MAE (error) are plotted against increasing training-set size under the same temporal CV.

Observed pattern:

- Training MAE rises from ~0.25 (very small samples) toward ~0.43 as more history is included — expected as the Ridge model stops memorizing tiny windows.
- Validation MAE settles near ~0.64 at the largest training size used by the curve, with a final train–val gap of ~0.21 on that plot.
- Under temporal CV summary, the train–val MAE gap is smaller (~0.09: 0.48 vs 0.57), with low fold-to-fold variance (val MAE std 0.06).

Neither curve collapses toward near-zero training error with a large persistent validation gap (classic overfitting), nor do both errors remain high and flat with almost no gap while capacity is obviously exhausted in a trivial sense without residual structure.

## Diagnosis: **well fitted**

Evidence:

1. **Cross-validation:** Train MAE (0.48 ± 0.03) and validation MAE (0.57 ± 0.06) are close on a 1–5 CSAT scale; the ~0.09 gap does not indicate severe overfitting.
2. **Learning curve:** As training size grows, training error increases toward the validation level rather than staying near zero — the model is not memorizing the early timeline.
3. **Stability:** Validation MAE standard deviation across five chronological folds is modest (0.06), consistent with stable temporal generalization for this feature set.

Residual error (~0.5–0.6 MAE) is consistent with discrete 1–5 scores plus noise in how customers rate closed incidents; the linear Ridge on main-effect categoricals already captures the dominant category/carrier structure.

## Corrective action (tied to this diagnosis)

Because the model is **well fitted** but still leaves ~0.57 mean absolute CSAT error, the next step should reduce *systematic* residual error in Last Mile incident types—not “collect more rows” without a reason.

**Action:** Add explicit **category × carrier** interaction features (e.g. `LOST_PARCEL` with `LOCAL_ES` vs `UPS`) before re-running the same 5-fold `TimeSeriesSplit`.  

**Why this addresses the residual:** CONTEXT.md / Last Mile notes that carrier performance and incident mix differ by market; main-effect one-hot encoding cannot express “lost parcel on a weak local carrier” vs “lost parcel on UPS.” Encoding those interactions targets the remaining structured bias in CSAT by incident–carrier pair while keeping the temporal evaluation protocol unchanged. Re-evaluate with MAE mean ± std; only if the train–val gap widens substantially should regularization (`Ridge` alpha) be increased.
