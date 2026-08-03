"use client";

import { useEffect, useState } from "react";
import { timedFetch } from "@/src/services/telemetry";

const API =
  process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type Report = {
  period: { from: string; to: string };
  metrics: Record<string, Array<Record<string, unknown>>>;
};

function MetricTable({
  title,
  rows,
}: {
  title: string;
  rows: Array<Record<string, unknown>>;
}) {
  const columns = rows.length ? Object.keys(rows[0]) : [];
  return (
    <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-lg font-medium">{title}</h2>
      </div>
      {!rows.length ? (
        <p className="px-4 py-6 text-sm text-slate-400">No data in period.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-800 text-slate-300">
            <tr>
              {columns.map((c) => (
                <th key={c} className="px-3 py-2 font-medium">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx} className="border-t border-slate-800">
                {columns.map((c) => (
                  <td key={c} className="px-3 py-2">
                    {String(row[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export default function TelemetryPage() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await timedFetch(`${API}/telemetry/report`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setReport(await res.json());
      } catch (err) {
        setError(String(err));
      }
    }
    void load();
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold">Telemetry report</h1>
        <p className="mt-2 text-slate-400">
          Technical operational metrics for the engineering team.
        </p>
        {report && (
          <p className="mt-2 text-sm text-cyan-300">
            Period: {report.period.from} → {report.period.to}
          </p>
        )}
      </header>
      {error && <p className="text-sm text-red-300">{error}</p>}
      {report &&
        Object.entries(report.metrics).map(([key, rows]) => (
          <MetricTable key={key} title={key} rows={rows} />
        ))}
    </main>
  );
}
