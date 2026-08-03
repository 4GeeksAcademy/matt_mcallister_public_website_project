"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function LoginPageContent() {
  const searchParams = useSearchParams();
  const resetStatus = searchParams.get("reset");

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-12 text-slate-100">
      <div className="mx-auto w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
        <h1 className="text-2xl font-semibold">Log in</h1>
        <p className="mt-2 text-sm text-slate-300">Use your credentials to access TrackFlow backoffice.</p>

        {resetStatus === "success" ? (
          <div className="mt-4 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
            Your password was reset successfully. You can now sign in.
          </div>
        ) : null}

        <form className="mt-6 space-y-4" onSubmit={(event) => event.preventDefault()}>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-300">Email</span>
            <input
              type="email"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 outline-none ring-cyan-400 transition focus:ring-2"
              placeholder="you@example.com"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block text-slate-300">Password</span>
            <input
              type="password"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 outline-none ring-cyan-400 transition focus:ring-2"
              placeholder="••••••••"
            />
          </label>

          <button
            type="submit"
            className="w-full rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950 transition hover:bg-cyan-400"
          >
            Sign in
          </button>
        </form>

        <p className="mt-4 text-sm text-slate-300">
          <Link href="/forgot-password" className="font-medium text-cyan-300 hover:text-cyan-200">
            Forgot your password?
          </Link>
        </p>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageContent />
    </Suspense>
  );
}