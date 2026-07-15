"use client";

import Link from "next/link";
import { useEffect } from "react";
import { initTelemetry, track } from "@/src/services/telemetry";

const LINKS = [
  { href: "/", label: "Executive" },
  { href: "/reporting", label: "Reporting" },
  { href: "/login", label: "Login" },
  { href: "/inventory", label: "Inventory" },
  { href: "/telemetry", label: "Telemetry" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    initTelemetry();
    const path = window.location.pathname;
    track("page_viewed", { path, title: document.title });
    const started = performance.now();
    const onLoad = () => {
      track("page_load_recorded", {
        path,
        duration_ms: Math.round(performance.now() - started),
      });
    };
    if (document.readyState === "complete") onLoad();
    else window.addEventListener("load", onLoad, { once: true });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <p className="text-sm font-semibold tracking-wide text-cyan-300">
            TrackFlow Backoffice
          </p>
          <nav className="flex flex-wrap gap-3 text-sm">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-slate-300 hover:text-white"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}
