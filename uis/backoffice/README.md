This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

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
- `RESEND_API_KEY` is required for actual password reset email delivery.
- `AUTH_STORE_FILE` lets you persist users and reset tokens across app restarts.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
