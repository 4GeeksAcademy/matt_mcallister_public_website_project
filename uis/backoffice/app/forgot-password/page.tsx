"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

const confirmationMessage = "If that address is registered, you'll receive a link shortly";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (hasSubmitted || isSubmitting) {
      return;
    }

    setIsSubmitting(true);

    try {
      await fetch("/auth/forgot-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });
    } finally {
      setIsSubmitting(false);
      setHasSubmitted(true);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-12 text-slate-100">
      <div className="mx-auto w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
        <h1 className="text-2xl font-semibold">Forgot password</h1>
        <p className="mt-2 text-sm text-slate-300">Enter your email to receive a reset link.</p>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-300">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={hasSubmitted}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 outline-none ring-cyan-400 transition focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60"
              placeholder="you@example.com"
            />
          </label>

          <button
            type="submit"
            disabled={hasSubmitted || isSubmitting}
            className="w-full rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:text-slate-300"
          >
            {isSubmitting ? "Sending..." : "Send reset link"}
          </button>
        </form>

        {hasSubmitted ? (
          <p className="mt-4 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
            {confirmationMessage}
          </p>
        ) : null}

        <p className="mt-4 text-sm text-slate-300">
          Remembered your password?{" "}
          <Link href="/login" className="font-medium text-cyan-300 hover:text-cyan-200">
            Back to login
          </Link>
        </p>
      </div>
    </main>
  );
}