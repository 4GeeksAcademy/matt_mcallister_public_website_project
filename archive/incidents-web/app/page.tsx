import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-16">
      <section className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ocean">
          TrackFlow Tech
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink md:text-5xl">
          Incident report analysis
        </h1>
        <p className="mt-4 text-lg text-slate-600">
          Upload the CX helpdesk export, review valid vs invalid records, and
          export Valentina&apos;s summary metrics for client reporting.
        </p>
        <Link
          href="/analyze"
          className="mt-8 inline-flex rounded-md bg-ocean px-5 py-3 text-sm font-semibold text-white hover:bg-[#00486c]"
        >
          Open incident analysis
        </Link>
      </section>
    </main>
  );
}
