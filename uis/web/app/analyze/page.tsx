"use client";

import { FormEvent, useState } from "react";
import {
  AnalysisResult,
  analyzeCsv,
  downloadResultsCsv,
} from "@/lib/api";

function BreakdownList({
  title,
  values,
  emptyLabel = "No data",
}: {
  title: string;
  values: Record<string, number>;
  emptyLabel?: string;
}) {
  const entries = Object.entries(values).sort(([a], [b]) => a.localeCompare(b));

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-ink">{title}</h2>
      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">{emptyLabel}</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm">
          {entries.map(([key, value]) => (
            <li key={key} className="flex items-center justify-between gap-4">
              <span className="text-slate-700">{key}</span>
              <span className="font-semibold text-ink">{value}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function AnalyzePage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setResult(null);

    if (!file) {
      setError("Choose a CSV file to analyze.");
      return;
    }

    setIsAnalyzing(true);
    try {
      const analysis = await analyzeCsv(file);
      setResult(analysis);
    } catch (uploadError) {
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "Unable to analyze the uploaded CSV.",
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const onExport = async () => {
    setError(null);
    setIsExporting(true);
    try {
      const blob = await downloadResultsCsv();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "results.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (exportError) {
      setError(
        exportError instanceof Error
          ? exportError.message
          : "Unable to export results.",
      );
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <header className="mb-8 max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ocean">
          CX · Valentina Cruz
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-ink md:text-4xl">
          Incident analysis
        </h1>
        <p className="mt-3 text-slate-600">
          Upload <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm">incidents-trackflow.csv</code>{" "}
          (or another UTF-8 CSV with the TrackFlow schema). Invalid rows are
          counted by rule; customer emails are never shown.
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="rounded-xl border border-dashed border-ocean/40 bg-white p-6 shadow-sm"
      >
        <label className="block text-sm font-medium text-slate-700" htmlFor="csv">
          Incident CSV
        </label>
        <input
          id="csv"
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="mt-2 block w-full text-sm text-slate-700 file:mr-4 file:rounded-md file:border-0 file:bg-seafoam/20 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-ink"
        />
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={isAnalyzing}
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white hover:bg-[#00486c] disabled:opacity-60"
          >
            {isAnalyzing ? "Analyzing…" : "Analyze CSV"}
          </button>
          <button
            type="button"
            onClick={() => void onExport()}
            disabled={isExporting || !result}
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-ink hover:bg-slate-50 disabled:opacity-60"
          >
            {isExporting ? "Exporting…" : "Download results CSV"}
          </button>
        </div>
      </form>

      {error ? (
        <div
          role="alert"
          className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
        >
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="mt-8 space-y-6">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-ink">Summary</h2>
            <p className="mt-1 text-sm text-slate-500">Source: {result.source_file}</p>
            <dl className="mt-4 grid gap-3 sm:grid-cols-3">
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Total</dt>
                <dd className="text-2xl font-semibold">{result.total_records}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Valid</dt>
                <dd className="text-2xl font-semibold text-emerald-700">
                  {result.valid_records}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Invalid</dt>
                <dd className="text-2xl font-semibold text-red-700">
                  {result.invalid_records}
                </dd>
              </div>
            </dl>
            <div className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-sm">
              <p className="font-medium text-ink">Satisfaction index (closed)</p>
              <p className="mt-1 text-slate-700">
                Scored incidents: {result.scored_incidents} of{" "}
                {result.status_counts.CLOSED ?? 0}
              </p>
              <p className="mt-1 text-slate-700">
                Average score:{" "}
                {result.satisfaction_average == null
                  ? "n/a"
                  : `${result.satisfaction_average.toFixed(2)} / 5.00`}
              </p>
            </div>
          </section>

          <div className="grid gap-4 md:grid-cols-2">
            <BreakdownList
              title="Invalid records by reason"
              values={result.invalid_breakdown}
              emptyLabel="No invalid records"
            />
            <BreakdownList title="By category" values={result.category_counts} />
            <BreakdownList title="By status" values={result.status_counts} />
            <BreakdownList title="By country" values={result.country_counts} />
            <BreakdownList
              title="Satisfaction score distribution"
              values={result.satisfaction_counts}
            />
          </div>
        </div>
      ) : null}
    </main>
  );
}
