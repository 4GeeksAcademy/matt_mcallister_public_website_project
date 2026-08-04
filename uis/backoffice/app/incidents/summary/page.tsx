"use client";

import { useEffect, useState } from "react";
import { asSummary, branchLabel, getFriendlyError } from "@/components/incidentDomain";
import { IncidentSummary } from "../../../../../packages/shared/types";

const SummaryCard = ({
  title,
  values,
  labelFn,
}: {
  title: string;
  values: Record<string, number>;
  labelFn?: (key: string) => string;
}) => (
  <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
    <h2 className="text-lg font-semibold text-cyan-200">{title}</h2>
    <ul className="mt-3 space-y-2 text-sm text-slate-200">
      {Object.entries(values).map(([key, value]) => (
        <li key={key} className="flex items-center justify-between">
          <span>{labelFn ? labelFn(key) : key}</span>
          <span className="font-semibold">{value}</span>
        </li>
      ))}
    </ul>
  </article>
);

export default function IncidentSummaryPage() {
  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/incidents/summary", { cache: "no-store" });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(getFriendlyError(payload, "Unable to load summary data."));
      }

      const data = asSummary(payload);

      if (!data) {
        throw new Error("Unable to load summary data.");
      }

      setSummary(data);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Unable to load summary data.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadSummary(), 0);
    return () => window.clearTimeout(timeout);
  }, []);

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10 text-slate-100 md:px-10">
      <header className="mb-6">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Incident Manager</p>
        <h1 className="mt-2 text-3xl font-semibold">Incident Summary</h1>
      </header>

      {isLoading ? (
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
          Loading summary metrics...
        </section>
      ) : error ? (
        <section className="rounded-2xl border border-red-300 bg-red-900/30 p-6 text-red-100">
          <p>{error}</p>
          <button
            onClick={() => void loadSummary()}
            className="mt-3 rounded-md border border-red-200 px-3 py-1"
          >
            Retry
          </button>
        </section>
      ) : summary ? (
        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <SummaryCard title="By Status" values={summary.by_status} />
          <SummaryCard title="By Category" values={summary.by_category} />
          <SummaryCard title="By Origin" values={summary.by_origin} />
          <SummaryCard title="By Branch" values={summary.by_branch} labelFn={branchLabel} />
        </section>
      ) : null}
    </main>
  );
}
