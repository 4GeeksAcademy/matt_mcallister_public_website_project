# TrackFlow Supplier Application

Canonical supplier directory UI for TrackFlow logistics partners.

- **Path:** `uis/application`
- **Local port:** 3002
- **API:** `NEXT_PUBLIC_SUPPLIER_API_URL` → `services/supplier-api` on port 8002

## Getting Started

```bash
npm install
npm run dev -- --port 3002
```

Open [http://localhost:3002](http://localhost:3002). The home page links to
`/suppliers` for register, filter, rate update, and status management.

```bash
npm run lint
npm run build -- --webpack
```
