import {
  buildExecutiveSnapshot,
  milestone2SampleInput,
} from "@/lib/milestone2";
import Link from "next/link";

export default function Home() {
  const snapshot = buildExecutiveSnapshot(milestone2SampleInput);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-10 md:px-10">
        <header className="space-y-2">
          <nav className="mb-2 flex gap-3 text-sm text-cyan-300">
            <Link className="underline-offset-4 hover:underline" href="/">
              Dashboard
            </Link>
            <Link className="underline-offset-4 hover:underline" href="/suppliers">
              Suppliers
            </Link>
          </nav>
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">
            TrackFlow Backoffice
          </p>
          <h1 className="text-3xl font-semibold md:text-4xl">
            Executive Operations Snapshot
          </h1>
          <p className="max-w-2xl text-slate-300">
            Values below are produced by the shared Milestone 2 business-logic
            module imported from the monorepo.
          </p>
        </header>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-sm text-slate-400">Global Shipment Volume</p>
            <p className="mt-2 text-2xl font-semibold">
              {snapshot.globalShipmentVolume.toLocaleString()}
            </p>
          </article>
          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-sm text-slate-400">On-Time Rate</p>
            <p className="mt-2 text-2xl font-semibold">
              {snapshot.globalOnTimeRate}%
            </p>
          </article>
          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-sm text-slate-400">Return Rate</p>
            <p className="mt-2 text-2xl font-semibold">
              {snapshot.globalReturnRate}%
            </p>
          </article>
          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-sm text-slate-400">Average CSAT</p>
            <p className="mt-2 text-2xl font-semibold">{snapshot.averageCsat}%</p>
          </article>
          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-sm text-slate-400">Performance Status</p>
            <p className="mt-2 text-2xl font-semibold text-cyan-300">
              {snapshot.performanceStatus}
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
              {snapshot.countryBreakdown.map((row) => (
                <tr key={row.country} className="border-t border-slate-800">
                  <td className="px-4 py-3">{row.country}</td>
                  <td className="px-4 py-3">{row.shipmentVolume.toLocaleString()}</td>
                  <td className="px-4 py-3">{row.onTimeRate}%</td>
                  <td className="px-4 py-3">{row.returnRate}%</td>
                  <td className="px-4 py-3">{row.customerSatisfaction}%</td>
                  <td className="px-4 py-3">${row.operatingCostUsd.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <footer className="text-sm text-slate-400">
          Total operating cost: ${snapshot.totalOperatingCostUsd.toLocaleString()}
        </footer>
      </main>
    </div>
  );
}
