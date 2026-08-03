import LeadForm from "@/components/LeadForm";
import {
  benefits,
  coverage,
  proofMetrics,
  quickFacts,
  services,
} from "@/components/siteData";

export default function Home() {
  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-ink focus:px-4 focus:py-2 focus:text-white"
      >
        Skip to main content
      </a>

      <header className="sticky top-0 z-40 border-b border-white/20 bg-ink/95 backdrop-blur-sm">
        <nav
          className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4"
          aria-label="Main navigation"
        >
          <a href="#home" className="font-display text-2xl font-bold tracking-tight text-white">
            TrackFlow
          </a>
          <ul className="flex items-center gap-5 text-sm font-medium text-white/90">
            <li><a className="nav-link" href="#home">Home</a></li>
            <li><a className="nav-link" href="#services">Services</a></li>
            <li><a className="nav-link" href="#coverage">Coverage</a></li>
            <li><a className="nav-link" href="#contact-form">Contact</a></li>
          </ul>
        </nav>
      </header>

      <main id="main-content">
        <section id="home" className="hero relative overflow-hidden" aria-labelledby="hero-title">
          <div className="hero-glow" aria-hidden="true"></div>
          <div className="mx-auto grid max-w-7xl gap-12 px-6 py-20 lg:grid-cols-2 lg:py-28">
            <div className="space-y-6">
              <p className="inline-flex items-center rounded-full bg-white/20 px-4 py-1 text-xs font-semibold uppercase tracking-wider text-white">
                Binational logistics operation
              </p>
              <h1 id="hero-title" className="font-display text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
                Logistics that scales with your e-commerce
              </h1>
              <p className="max-w-xl text-lg leading-relaxed text-white/90">
                Warehouse management, last-mile deliveries, and reverse logistics in the United States and Spain. Over 15 years helping fashion, electronics, and cosmetics brands grow without worrying about operations.
              </p>
              <div className="flex flex-wrap gap-4">
                <a href="#contact-form" className="rounded-md bg-amber px-6 py-3 text-sm font-semibold text-ink transition hover:bg-yellow-300 focus:outline-none focus:ring-2 focus:ring-white">
                  Request information
                </a>
                <a href="#services" className="rounded-md border border-white/60 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white">
                  Explore services
                </a>
              </div>
            </div>

            <aside className="panel rounded-2xl p-6 text-white" aria-label="TrackFlow quick facts">
              <h2 className="font-display text-2xl font-semibold">At a glance</h2>
              <dl className="mt-5 grid gap-4 sm:grid-cols-2">
                {quickFacts.map((fact) => (
                  <div key={fact.label}>
                    <dt className="text-xs uppercase tracking-wider text-white/70">{fact.label}</dt>
                    <dd className="text-2xl font-semibold">{fact.value}</dd>
                  </div>
                ))}
              </dl>
            </aside>
          </div>
        </section>

        <section id="services" className="mx-auto max-w-7xl px-6 py-16" aria-labelledby="services-title">
          <div className="mb-10 max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-ocean">Our services</p>
            <h2 id="services-title" className="font-display text-3xl font-bold text-ink sm:text-4xl">
              Built for e-commerce operations with real-world complexity
            </h2>
            <p className="mt-3 text-base text-ink/80">
              Answer-first summary: TrackFlow gives online brands a single logistics partner for storage, delivery, and returns in the US and Spain.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {services.map((service) => (
              <article key={service.title} className="card rounded-2xl p-6">
                <h3 className="font-display text-2xl font-semibold">{service.title}</h3>
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-relaxed text-ink/85">
                  {service.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section id="coverage" className="bg-white/70 py-16" aria-labelledby="coverage-title">
          <div className="mx-auto max-w-7xl px-6">
            <h2 id="coverage-title" className="font-display text-3xl font-bold text-ink sm:text-4xl">Coverage</h2>
            <div className="mt-8 grid gap-6 md:grid-cols-2">
              {coverage.map((region) => (
                <article key={region.country} className="card rounded-2xl p-6">
                  <h3 className="font-display text-2xl font-semibold">{region.country}</h3>
                  <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ink/85">
                    {region.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-6 py-16" aria-labelledby="benefits-title">
          <h2 id="benefits-title" className="font-display text-3xl font-bold text-ink sm:text-4xl">Why TrackFlow</h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {benefits.map((benefit) => (
              <article key={benefit.title} className="card rounded-2xl p-5">
                <h3 className="text-lg font-semibold">{benefit.title}</h3>
                <p className="mt-2 text-sm text-ink/80">{benefit.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="bg-ink py-16 text-white" aria-labelledby="proof-title">
          <div className="mx-auto max-w-7xl px-6">
            <h2 id="proof-title" className="font-display text-3xl font-bold sm:text-4xl">Proof-oriented operations</h2>
            <p className="mt-3 max-w-3xl text-white/80">
              We continuously track delivery performance, incident rates, and returns patterns to improve decision making. Data references used in this website are based on internal operational snapshots for demonstration purposes.
            </p>
            <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {proofMetrics.map((metric) => (
                <div key={metric.label} className="rounded-xl border border-white/20 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-wide text-white/70">{metric.label}</p>
                  <p className="mt-2 text-2xl font-semibold">{metric.value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="contact-form" className="mx-auto max-w-7xl px-6 py-16" aria-labelledby="contact-title">
          <div className="grid gap-8 lg:grid-cols-[1fr,1.4fr]">
            <div>
              <h2 id="contact-title" className="font-display text-3xl font-bold text-ink sm:text-4xl">Request information</h2>
              <p className="mt-3 text-sm leading-relaxed text-ink/80">
                This form is designed for e-commerce companies looking to outsource logistics operations. If you are an end consumer tracking a package or return, please contact your brand directly.
              </p>
              <div className="mt-8 rounded-2xl bg-white p-6 shadow-sm">
                <h3 className="font-display text-xl font-semibold">Contact</h3>
                <ul className="mt-3 space-y-2 text-sm text-ink/85">
                  <li>Email: <a href="mailto:comercial@trackflow.com" className="link">comercial@trackflow.com</a></li>
                  <li>Los Angeles: <a href="tel:+12135550147" className="link">+1 213 555 0147</a></li>
                  <li>Zaragoza: <a href="tel:+34976123456" className="link">+34 976 123 456</a></li>
                </ul>
              </div>
            </div>
            <LeadForm />
          </div>
        </section>
      </main>

      <footer className="border-t border-ink/10 bg-white py-6">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-3 px-6 text-sm text-ink/80 md:flex-row md:items-center">
          <p>© 2025 TrackFlow. All rights reserved.</p>
          <a href="https://linkedin.com/company/trackflow" className="link" rel="noopener noreferrer" target="_blank">LinkedIn</a>
        </div>
      </footer>
    </>
  );
}
