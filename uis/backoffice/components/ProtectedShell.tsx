"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";

import { hasValidSession, logout } from "@/lib/auth";

export default function ProtectedShell({ children }: PropsWithChildren) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready] = useState(() => hasValidSession());

  useEffect(() => {
    if (!hasValidSession()) {
      router.replace("/login");
    }
  }, [router]);

  const links = useMemo(
    () => [
      { href: "/", label: "Dashboard" },
      { href: "/account/profile", label: "Profile" },
      { href: "/account/change-password", label: "Change password" },
    ],
    []
  );

  if (!ready) {
    return (
      <div className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
        <p className="mx-auto max-w-3xl rounded-lg border border-slate-700 bg-slate-900 p-4 text-sm">
          Checking your session...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/90">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4 md:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">
            TrackFlow Backoffice
          </p>
          <button
            className="rounded-md border border-slate-600 px-3 py-1.5 text-sm transition hover:border-slate-400"
            onClick={logout}
            type="button"
          >
            Logout
          </button>
        </div>
        <nav className="mx-auto flex w-full max-w-6xl gap-3 px-6 pb-4 md:px-10">
          {links.map((link) => {
            const isActive = pathname === link.href;

            return (
              <Link
                key={link.href}
                className={`rounded-md px-3 py-1.5 text-sm ${
                  isActive
                    ? "bg-cyan-500/20 text-cyan-200"
                    : "text-slate-300 transition hover:bg-slate-800"
                }`}
                href={link.href}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
