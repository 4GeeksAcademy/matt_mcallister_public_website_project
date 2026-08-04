"use client";

import { useCallback, useEffect, useState } from "react";

const API =
  process.env.NEXT_PUBLIC_OPERATIONS_API_URL || "http://127.0.0.1:8005";

type WeeklyEntry = {
  warehouse: string;
  client_id: string;
  inbound_units_count: number;
  outbound_orders_count: number;
  stockout_events_count: number;
  discrepancy_events_count: number;
  discrepancy_rate: number;
};

type WeeklyReport = {
  week_start: string | null;
  entries: WeeklyEntry[];
};

type PipelineRun = {
  id?: string;
  week_start?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  records_processed?: number | null;
  status: string;
  error_message?: string | null;
};

function formatRate(rate: number): string {
  return `${(rate * 100).toFixed(2)}%`;
}

function warehouseLabel(warehouse: string): string {
  if (warehouse === "los_angeles") return "Los Angeles";
  if (warehouse === "zaragoza") return "Zaragoza";
  return warehouse;
}

export default function ReportingPage() {
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [latestRun, setLatestRun] = useState<PipelineRun | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const [perfRes, runRes] = await Promise.all([
        fetch(`${API}/reporting/weekly-warehouse-client-performance`),
        fetch(`${API}/reporting/pipeline-runs/latest`),
      ]);
      if (!perfRes.ok) throw new Error(`KPI HTTP ${perfRes.status}`);
      setReport(await perfRes.json());
      if (runRes.ok) {
        setLatestRun(await runRes.json());
      } else if (runRes.status !== 404) {
        throw new Error(`Run status HTTP ${runRes.status}`);
      } else {
        setLatestRun(null);
      }
    } catch (err) {
      setError(String(err));
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  async function triggerRun() {
    setRunning(true);
    setError("");
    try {
      const res = await fetch(`${API}/reporting/pipeline-runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ week_start: "2026-07-06" }),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`Trigger failed HTTP ${res.status}: ${detail}`);
      }
      await load();
    } catch (err) {
      setError(String(err));
    } finally {
      setRunning(false);
    }
  }

  const totals = (report?.entries ?? []).reduce(
    (acc, row) => ({
      inbound: acc.inbound + row.inbound_units_count,
      outbound: acc.outbound + row.outbound_orders_count,
      stockouts: acc.stockouts + row.stockout_events_count,
      discrepancies: acc.discrepancies + row.discrepancy_events_count,
    }),
    { inbound: 0, outbound: 0, stockouts: 0, discrepancies: 0 },
  );
  const overallDiscrepancyRate =
    totals.outbound > 0 ? totals.discrepancies / totals.outbound : 0;

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">
            Weekly Warehouse &amp; Client Performance
          </h1>
          <p className="mt-2 max-w-2xl text-slate-400">
            Monday executive rollup for Thomas and Ana — inbound volume, outbound
            throughput, stockout frequency, and discrepancy rate by warehouse and
            client.
          </p>
          {report?.week_start && (
            <p className="mt-2 text-sm text-cyan-300">
              Week starting Monday {report.week_start} (UTC)
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => void triggerRun()}
          disabled={running}
          className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
        >
          {running ? "Running pipeline…" : "Run weekly pipeline"}
        </button>
      </header>

      {error && <p className="text-sm text-red-300">{error}</p>}

      {latestRun && (
        <p className="text-sm text-slate-400">
          Last pipeline run:{" "}
          <span className="text-slate-200">{latestRun.status}</span>
          {latestRun.records_processed != null &&
            ` · ${latestRun.records_processed} rows`}
          {latestRun.finished_at && ` · finished ${latestRun.finished_at}`}
        </p>
      )}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Inbound Volume"
          value={totals.inbound.toLocaleString()}
          hint="Units received"
        />
        <KpiCard
          label="Outbound Throughput"
          value={totals.outbound.toLocaleString()}
          hint="Orders dispatched"
        />
        <KpiCard
          label="Stockout Frequency"
          value={totals.stockouts.toLocaleString()}
          hint="Threshold events"
        />
        <KpiCard
          label="Discrepancy Rate"
          value={formatRate(overallDiscrepancyRate)}
          hint={`${totals.discrepancies} discrepancy events`}
        />
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <div className="border-b border-slate-800 px-4 py-3">
          <h2 className="text-lg font-medium">
            Performance by warehouse and client
          </h2>
        </div>
        {!report?.entries?.length ? (
          <p className="px-4 py-6 text-sm text-slate-400">
            No weekly rows yet. Run the pipeline to populate this report.
          </p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800 text-slate-300">
              <tr>
                <th className="px-3 py-2 font-medium">Warehouse</th>
                <th className="px-3 py-2 font-medium">Client</th>
                <th className="px-3 py-2 font-medium">Inbound Volume</th>
                <th className="px-3 py-2 font-medium">Outbound Throughput</th>
                <th className="px-3 py-2 font-medium">Stockout Frequency</th>
                <th className="px-3 py-2 font-medium">Discrepancy Rate</th>
              </tr>
            </thead>
            <tbody>
              {report.entries.map((row) => (
                <tr
                  key={`${row.warehouse}-${row.client_id}`}
                  className="border-t border-slate-800"
                >
                  <td className="px-3 py-2">{warehouseLabel(row.warehouse)}</td>
                  <td className="px-3 py-2">{row.client_id}</td>
                  <td className="px-3 py-2">
                    {row.inbound_units_count.toLocaleString()}
                  </td>
                  <td className="px-3 py-2">
                    {row.outbound_orders_count.toLocaleString()}
                  </td>
                  <td className="px-3 py-2">
                    {row.stockout_events_count.toLocaleString()}
                  </td>
                  <td className="px-3 py-2">
                    {formatRate(row.discrepancy_rate)}
                    <span className="ml-2 text-slate-500">
                      ({row.discrepancy_events_count})
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}

function KpiCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-5">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-50">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{hint}</p>
    </div>
  );
}
