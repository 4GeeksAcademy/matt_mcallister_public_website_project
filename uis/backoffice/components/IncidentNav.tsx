"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Executive" },
  { href: "/incidents/register", label: "Register Incident" },
  { href: "/incidents", label: "Incidents" },
  { href: "/incidents/summary", label: "Summary" },
];

export default function IncidentNav() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-slate-800 bg-slate-950/80 px-4 py-3 backdrop-blur md:px-8">
      <ul className="mx-auto flex w-full max-w-6xl flex-wrap gap-2">
        {links.map((item) => {
          const active = pathname === item.href;

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`inline-flex rounded-md border px-3 py-2 text-sm transition ${
                  active
                    ? "border-cyan-300 bg-cyan-300/20 text-cyan-100"
                    : "border-slate-700 bg-slate-900 text-slate-200 hover:border-cyan-500"
                }`}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
