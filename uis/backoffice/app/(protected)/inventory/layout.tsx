"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PropsWithChildren } from "react";

const links = [
  { href: "/inventory/products", label: "SKU catalog" },
  { href: "/inventory/orders/inbound", label: "Inbound receipt" },
  { href: "/inventory/orders/outbound", label: "Outbound pick" },
  { href: "/inventory/orders", label: "Stock movements" },
];

export default function InventoryLayout({ children }: PropsWithChildren) {
  const pathname = usePathname();

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10 md:px-10">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Warehouse operations</p>
        <h1 className="text-2xl font-semibold md:text-3xl">Inventory</h1>
        <p className="max-w-2xl text-sm text-slate-300">
          Live SKU stock across the Los Angeles and Zaragoza warehouses. Record inbound
          receipts and outbound picks, then review the movement history.
        </p>
      </header>

      <nav className="mt-6 flex flex-wrap gap-2" aria-label="Inventory sections">
        {links.map((link) => {
          const isActive = pathname === link.href;

          return (
            <Link
              key={link.href}
              className={`rounded-md px-3 py-1.5 text-sm ${
                isActive
                  ? "bg-cyan-500/20 text-cyan-200"
                  : "border border-slate-700 text-slate-300 transition hover:bg-slate-800"
              }`}
              href={link.href}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-8">{children}</div>
    </div>
  );
}
