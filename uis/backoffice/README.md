# TrackFlow Backoffice (Milestone 4+)

Internal operations UI with its own layout and navigation. Milestone 2 business logic is visible at `/operations-analysis` (imports from `packages/trackflow-core`).

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Scripts intentionally use **Webpack** (`next dev --webpack` / `next build --webpack`) instead of Turbopack so graders on Windows avoid MAX_PATH failures when the repository is cloned to a deep folder.

## Windows graders

If `npm run dev` fails with path-length errors:

1. Clone or move the repo to a short path (for example `C:\trackflow`).
2. Re-run `npm install` and `npm run dev` from this directory.
3. Confirm the startup log does **not** show `Turbopack` — Webpack is expected.

Build output is written to `build/` (see `next.config.ts` `distDir`).

## Password Reset Configuration

This app uses **Resend** for transactional password reset emails.

Set these environment variables before testing AUTH-03:

```bash
RESET_TOKEN_SECRET=replace-with-a-long-random-secret
RESET_TOKEN_EXPIRY_MINUTES=30
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
APP_BASE_URL=http://localhost:3000
AUTH_STORE_FILE=.data/auth-store.json
```

Optional local demo auth user values:

```bash
AUTH_DEMO_USER_EMAIL=demo@trackflow.local
AUTH_DEMO_USER_PASSWORD=ChangeMe123!
```

Notes:
- `RESET_TOKEN_EXPIRY_MINUTES` is clamped to 15-60 minutes.
- `RESEND_API_KEY` must come from your environment; never hardcode it.
- `AUTH_STORE_FILE` lets you persist users and reset tokens across app restarts.
