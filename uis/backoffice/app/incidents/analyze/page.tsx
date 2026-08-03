"use client";

import { FormEvent, useState } from "react";
import {
  AnalysisResult,
  analyzeCsv,
  downloadResultsCsv,
} from "@/lib/incident-analysis";

function Breakdown({
  title,
  values,
}: {
  title: string;
  values: Record<string, number>;
}) {
  const entries = Object.entries(values).sort(([a], [b]) => a.localeCompare(b));
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
      {entries.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {entries.map(([key, value]) => (
            <li key={key} className="flex justify-between gap-4">
              <span className="text-slate-300">{key}</span>
              <span className="font-semibold text-slate-100">{value}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-400">No data</p>
      )}
    </section>
  );
}

export default function AnalyzeIncidentsPage() {
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
      setResult(await analyzeCsv(file));
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
      anchor.download = "incident-analysis.csv";
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
    <main className="mx-auto w-full max-w-5xl px-6 py-10 text-slate-100">
      <header className="mb-8 max-w-2xl">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">
          Incident Manager
        </p>
        <h1 className="mt-2 text-3xl font-semibold">Analyze Incident CSV</h1>
        <p className="mt-3 text-slate-300">
          Upload a UTF-8 CSV using the TrackFlow incident schema. Invalid rows
          are grouped by rule and customer emails are never displayed.
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="rounded-xl border border-dashed border-cyan-400/40 bg-slate-900 p-6"
      >
        <label className="block text-sm font-medium" htmlFor="csv">
          Incident CSV
        </label>
        <input
          id="csv"
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="mt-2 block w-full text-sm text-slate-300 file:mr-4 file:rounded-md file:border-0 file:bg-cyan-900/50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-cyan-100"
        />
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={isAnalyzing}
            className="rounded-md bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-500 disabled:opacity-60"
          >
            {isAnalyzing ? "Analyzing…" : "Analyze CSV"}
          </button>
          <button
            type="button"
            onClick={() => void onExport()}
            disabled={isExporting || !result}
            className="rounded-md border border-slate-600 px-4 py-2 text-sm font-semibold hover:bg-slate-800 disabled:opacity-60"
          >
            {isExporting ? "Exporting…" : "Download results CSV"}
          </button>
        </div>
      </form>

      {error ? (
        <div
          role="alert"
          className="mt-6 rounded-md border border-red-500/50 bg-red-950/40 px-4 py-3 text-sm text-red-200"
        >
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="mt-8 space-y-6">
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h2 className="text-lg font-semibold">Summary</h2>
            <p className="mt-1 text-sm text-slate-400">
              Source: {result.source_file}
            </p>
            <dl className="mt-4 grid gap-3 sm:grid-cols-3">
              <div>
                <dt className="text-xs uppercase text-slate-400">Total</dt>
                <dd className="text-2xl font-semibold">{result.total_records}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-slate-400">Valid</dt>
                <dd className="text-2xl font-semibold text-emerald-400">
                  {result.valid_records}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-slate-400">Invalid</dt>
                <dd className="text-2xl font-semibold text-red-400">
                  {result.invalid_records}
                </dd>
              </div>
            </dl>
            <p className="mt-4 text-sm text-slate-300">
              Closed-incident satisfaction:{" "}
              {result.satisfaction_average == null
                ? "n/a"
                : `${result.satisfaction_average.toFixed(2)} / 5.00`}{" "}
              ({result.scored_incidents} scored)
            </p>
          </section>

          <div className="grid gap-4 md:grid-cols-2">
            <Breakdown title="Invalid records by reason" values={result.invalid_breakdown} />
            <Breakdown title="By category" values={result.category_counts} />
            <Breakdown title="By status" values={result.status_counts} />
            <Breakdown title="By country" values={result.country_counts} />
            <Breakdown title="Satisfaction scores" values={result.satisfaction_counts} />
          </div>
        </div>
      ) : null}
    </main>
  );
}
