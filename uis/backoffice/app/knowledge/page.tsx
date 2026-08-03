"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

type Theme = "light" | "dark";

export default function KnowledgePage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const stored = window.localStorage.getItem("trackflow-theme");
    if (stored === "light" || stored === "dark") {
      setTheme(stored);
      return;
    }
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setTheme(prefersDark ? "dark" : "light");
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("trackflow-theme", theme);
  }, [theme]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    const apiBase =
      process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
      "http://localhost:8001";

    try {
      const response = await fetch(`${apiBase}/knowledge/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(
          detail || `Request failed with status ${response.status}`,
        );
      }

      const data = (await response.json()) as { answer?: string };
      if (typeof data.answer !== "string" || !data.answer.trim()) {
        throw new Error("The API returned an empty answer.");
      }
      setAnswer(data.answer);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unexpected error talking to the API.";
      setError(message);
      setAnswer(null);
    } finally {
      setLoading(false);
    }
  }

  const isDark = theme === "dark";

  return (
    <div
      className={
        isDark
          ? "min-h-screen bg-slate-950 text-slate-100"
          : "min-h-screen bg-slate-50 text-slate-900"
      }
    >
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-6 py-10 md:px-10">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <p
              className={
                isDark
                  ? "text-xs uppercase tracking-[0.2em] text-cyan-300"
                  : "text-xs uppercase tracking-[0.2em] text-cyan-700"
              }
            >
              TrackFlow Backoffice
            </p>
            <h1 className="text-3xl font-semibold md:text-4xl">
              Commercial Knowledge Assistant
            </h1>
            <p className={isDark ? "max-w-2xl text-slate-300" : "max-w-2xl text-slate-600"}>
              Ask the way a TrackFlow salesperson would on a client call. Answers
              come from the indexed commercial knowledge base.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className={
                isDark
                  ? "text-sm text-cyan-300 underline-offset-4 hover:underline"
                  : "text-sm text-cyan-800 underline-offset-4 hover:underline"
              }
            >
              Snapshot
            </Link>
            <button
              type="button"
              onClick={() => setTheme(isDark ? "light" : "dark")}
              className={
                isDark
                  ? "rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200"
                  : "rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700"
              }
            >
              {isDark ? "Light mode" : "Dark mode"}
            </button>
          </div>
        </header>

        <form
          onSubmit={onSubmit}
          className={
            isDark
              ? "space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-5"
              : "space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          }
        >
          <label className="block space-y-2">
            <span className="text-sm font-medium">Question</span>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              placeholder="e.g. What's the standard return window?"
              className={
                isDark
                  ? "w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-cyan-500"
                  : "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-cyan-600"
              }
            />
          </label>
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className={
              isDark
                ? "rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
                : "rounded-xl bg-cyan-700 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            }
          >
            {loading ? "Asking…" : "Ask"}
          </button>
        </form>

        {loading ? (
          <p className={isDark ? "text-slate-400" : "text-slate-500"}>
            Retrieving context and generating an answer…
          </p>
        ) : null}

        {error ? (
          <div
            role="alert"
            className={
              isDark
                ? "rounded-2xl border border-red-900/60 bg-red-950/40 p-4 text-red-200"
                : "rounded-2xl border border-red-200 bg-red-50 p-4 text-red-800"
            }
          >
            <p className="font-medium">Could not get an answer</p>
            <p className="mt-1 text-sm">{error}</p>
          </div>
        ) : null}

        {answer ? (
          <section
            className={
              isDark
                ? "rounded-2xl border border-slate-800 bg-slate-900 p-5"
                : "rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
            }
          >
            <h2 className="text-sm font-medium uppercase tracking-wide opacity-70">
              Answer
            </h2>
            <p className="mt-3 whitespace-pre-wrap leading-relaxed">{answer}</p>
          </section>
        ) : null}
      </main>
    </div>
  );
}
