import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-16 text-slate-100">
      <div className="mx-auto max-w-5xl">
        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">
          TrackFlow
        </p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold md:text-6xl">
          Keep logistics partners and operations moving together.
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-slate-300">
          Use the application workspace to manage the supplier relationships that
          support TrackFlow&apos;s logistics network.
        </p>

        <section className="mt-12 grid gap-5 md:grid-cols-2">
          <Link
            className="rounded-2xl border border-cyan-800 bg-cyan-950/30 p-6 transition hover:border-cyan-500 hover:bg-cyan-950/50"
            href="/suppliers"
          >
            <h2 className="text-2xl font-semibold text-cyan-200">Supplier directory</h2>
            <p className="mt-3 text-slate-300">
              Register suppliers, filter the directory, update rates, and manage
              partner status for the USA and Spain.
            </p>
            <p className="mt-5 text-sm font-semibold text-cyan-300">
              Open supplier directory →
            </p>
          </Link>
        </section>
      </div>
    </main>
  );
}
