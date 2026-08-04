# TrackFlow Public Website

This app is a shareable static website for TrackFlow's Milestone 1 requirements.

## Included

- Responsive landing page with required sections and content order.
- Fully validated lead form with exact error messages and success state.
- Warning for low volume submissions (0-100 shipments/month).
- SEO metadata (title, description, canonical, Open Graph, Twitter).
- Required Schema.org Organization JSON-LD.
- Accessibility-first markup (semantic sections, labels, focus styles, skip link).
- Local lead scoring simulation with normalized payload output in browser console.

## Run locally

Option 1 (fastest):

1. Open `index.html` directly in your browser.

Option 2 (recommended):

1. From this folder, run:

```bash
python3 -m http.server 8080
```

2. Open `http://localhost:8080` in your browser.

## Files

- `index.html`: page structure, SEO tags, schema markup.
- `styles.css`: visual theme, custom utility styles.
- `script.js`: client-side validation, warning logic, lead scoring simulation.
- `robots.txt`: crawler directives.
- `sitemap.xml`: static sitemap for indexing.

## Deploy to Vercel

Deploy from this folder so Vercel treats this app as the project root:

```bash
cd apps/trackflow-website
npx vercel
```

For a production deployment:

```bash
cd apps/trackflow-website
npx vercel --prod
```

Notes:

- The first command links this directory to a Vercel project.
- If Vercel asks for framework preset, choose `Other`.
- Build command can be left empty for this static site.
