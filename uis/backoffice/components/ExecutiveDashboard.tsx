"use client";

import type { ExecutiveSnapshot } from "../../../packages/shared/business-logic/milestone2";
import { useEffect, useState } from "react";
import { apiUrls, parseApiError } from "../lib/api";

type LoadState =
  | { phase: "loading" }
  | { phase: "fulfilled"; snapshot: ExecutiveSnapshot }
  | { phase: "rejected"; message: string };

const formatNumber = (value: number | undefined, fallback = "—") =>
  value != null ? value.toLocaleString() : fallback;

const formatPercent = (value: number | undefined, fallback = "—") =>
  value != null ? `${value}%` : fallback;

export default function ExecutiveDashboard() {
  const [loadState, setLoadState] = useState<LoadState>({ phase: "loading" });

  useEffect(() => {
    let cancelled = false;

    const loadSnapshot = async () => {
      setLoadState({ phase: "loading" });

      try {
        const response = await fetch(apiUrls.executiveSnapshot);

        if (!response.ok) {
          const message = await parseApiError(response);
          if (!cancelled) {
            setLoadState({ phase: "rejected", message });
          }
          return;
        }

        const body = (await response.json()) as { data?: ExecutiveSnapshot };
        const snapshot = body.data;

        if (!snapshot?.countryBreakdown?.length) {
          if (!cancelled) {
            setLoadState({
              phase: "rejected",
              message:
                "Snapshot data is incomplete. Please refresh the page or contact your administrator.",
            });
          }
          return;
        }

        if (!cancelled) {
          setLoadState({ phase: "fulfilled", snapshot });
        }
      } catch {
        if (!cancelled) {
          setLoadState({
            phase: "rejected",
            message:
              "We could not reach the server. Make sure the API is running and refresh this page.",
          });
        }
      }
    };

    loadSnapshot();

    return () => {
      cancelled = true;
    };
  }, []);

  if (loadState.phase === "loading") {
    return (
      <div
        className="flex min-h-[40vh] items-center justify-center text-slate-300"
        role="status"
        aria-live="polite"
      >
        Loading executive snapshot…
      </div>
    );
  }

  if (loadState.phase === "rejected") {
    return (
      <div
        className="rounded-2xl border border-red-800 bg-red-950/40 p-6 text-red-200"
        role="alert"
      >
        <h2 className="text-lg font-semibold">Unable to load dashboard</h2>
        <p className="mt-2 text-sm">{loadState.message}</p>
        <button
          type="button"
          className="mt-4 rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500"
          onClick={() => window.location.reload()}
        >
          Refresh page
        </button>
      </div>
    );
  }

  const snapshot = loadState.snapshot;

  return (
    <>
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-sm text-slate-400">Global Shipment Volume</p>
          <p className="mt-2 text-2xl font-semibold">
            {formatNumber(snapshot?.globalShipmentVolume)}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-sm text-slate-400">On-Time Rate</p>
          <p className="mt-2 text-2xl font-semibold">
            {formatPercent(snapshot?.globalOnTimeRate)}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-sm text-slate-400">Return Rate</p>
          <p className="mt-2 text-2xl font-semibold">
            {formatPercent(snapshot?.globalReturnRate)}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-sm text-slate-400">Average CSAT</p>
          <p className="mt-2 text-2xl font-semibold">
            {formatPercent(snapshot?.averageCsat)}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-sm text-slate-400">Performance Status</p>
          <p className="mt-2 text-2xl font-semibold text-cyan-300">
            {snapshot?.performanceStatus ?? "Unknown"}
          </p>
        </article>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-800 text-slate-300">
            <tr>
              <th className="px-4 py-3 font-medium">Country</th>
              <th className="px-4 py-3 font-medium">Shipment Volume</th>
              <th className="px-4 py-3 font-medium">On-Time %</th>
              <th className="px-4 py-3 font-medium">Returns %</th>
              <th className="px-4 py-3 font-medium">CSAT %</th>
              <th className="px-4 py-3 font-medium">Cost (USD)</th>
            </tr>
          </thead>
          <tbody>
            {(snapshot?.countryBreakdown ?? []).map((row) => (
              <tr key={row?.country ?? "unknown"} className="border-t border-slate-800">
                <td className="px-4 py-3">{row?.country ?? "—"}</td>
                <td className="px-4 py-3">{formatNumber(row?.shipmentVolume)}</td>
                <td className="px-4 py-3">{formatPercent(row?.onTimeRate)}</td>
                <td className="px-4 py-3">{formatPercent(row?.returnRate)}</td>
                <td className="px-4 py-3">{formatPercent(row?.customerSatisfaction)}</td>
                <td className="px-4 py-3">
                  ${formatNumber(row?.operatingCostUsd)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <footer className="text-sm text-slate-400">
        Total operating cost: $
        {formatNumber(snapshot?.totalOperatingCostUsd)}
      </footer>
    </>
  );
}
