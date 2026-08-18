# TrackFlow Public Website (Milestone 4)

Next.js App Router corporate site for TrackFlow logistics.

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
