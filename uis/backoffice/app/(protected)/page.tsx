import Link from "next/link";

export default function DashboardPage() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10 md:px-10">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold md:text-4xl">
          TrackFlow Operations
        </h1>
        <p className="max-w-3xl text-slate-300">
          Review warehouse health and compare carrier recommendations generated
          by the canonical Milestone 2 business logic.
        </p>
      </header>

      <Link
        href="/operations-analysis"
        className="group rounded-2xl border border-cyan-700/70 bg-cyan-950/30 p-6 transition hover:border-cyan-400"
      >
        <p className="text-sm font-medium text-cyan-300">Operations analysis</p>
        <h2 className="mt-2 text-xl font-semibold">
          Open carrier &amp; inventory analysis
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-slate-300">
          See inventory value, low-stock alerts, warehouse totals, carrier
          reliability, shipment suitability scores, and estimated shipping costs.
        </p>
        <span className="mt-4 inline-block text-sm text-cyan-300 group-hover:text-cyan-200">
          View analysis →
        </span>
      </Link>
    </main>
  );
}
