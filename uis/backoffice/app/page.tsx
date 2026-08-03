import ExecutiveDashboard from "@/components/ExecutiveDashboard";

export default function Home() {
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
            module and loaded from the TrackFlow API.
          </p>
        </header>

        <ExecutiveDashboard />
      </main>
    </div>
  );
}
