# TrackFlow — Company Context for Model Evaluation

This extract supports metric selection and business-cost reasoning for regression evaluation. Full company briefing: [`CONTEXT.md`](CONTEXT.md).

## Business that depends on prediction quality

TrackFlow is a last-mile delivery and warehouse company operating in the **United States** and **Spain** (warehouses in Los Angeles and Zaragoza). Client contracts renew annually. Renewals are won or lost based on whether brand clients feel logistics operations are running well.

Executive KPIs explicitly include **CSAT (customer satisfaction)**, on-time delivery, costs, returns, and shipment volume. Customer Experience handles both **B2B** brands and **B2C** end consumers. Last Mile / Carrier Management tracks incidents such as lost parcels, delayed deliveries, wrong addresses, returns, and damage across carriers including UPS, FedEx, DHL (US), MRW, SEUR, and DHL (Spain), plus local Spanish carriers.

## Cost of prediction errors on `satisfaction_score`

When we model closed-incident **`satisfaction_score`** (1–5):

- **Typical absolute errors** (e.g. predicting 4 when the true score is 3) distort CX dashboards and weekly executive reporting. Account managers and Valentina Cruz’s CX team act on *average* perceived quality; a consistent bias of ~0.5–1 point on the typical ticket mis-prioritizes coaching, carrier reviews, and escalation.
- **Rare large errors** (e.g. predicting 5 when the true score is 1) matter for individual tickets, but day-to-day renewal risk and ops steering are driven by aggregate CSAT trends, not isolated catastrophic misses.
- **Client renewal** (Commercial / Miguel Torres) hinges on whether brands *feel* operations are healthy. Mis-estimating typical CSAT by a full point can hide churn risk or falsely trigger panic—both expensive relative to one outlier ticket.

Therefore, for TrackFlow’s business cost of errors on CSAT-style scores, **MAE** (mean absolute error) better reflects the cost of being wrong on a typical incident than **RMSE**, which overweight rare large residuals. RMSE remains useful as a secondary check for outlier-heavy failure modes (e.g. systematic mis-scoring of `LOST_PARCEL` or `DAMAGE`).
