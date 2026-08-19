"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  InventoryApiError,
  inventoryApi,
  warehouseLabel,
  type Product,
} from "@/lib/inventory";

/**
 * Stock-level indicators use each SKU's `low_stock_threshold` from the inventory API
 * (CONTEXT.md: warehouse ops need low-stock alerts for clients and procurement).
 * Healthy = current_stock > low_stock_threshold (green).
 * Low = current_stock <= low_stock_threshold (amber).
 * Depleted = current_stock === 0 (red).
 */
function stockStatus(product: Product) {
  if (product.current_stock <= 0) {
    return {
      label: "Depleted",
      className: "border-red-700 bg-red-900/40 text-red-200",
    };
  }

  if (product.current_stock <= product.low_stock_threshold) {
    return {
      label: "Low stock",
      className: "border-amber-700 bg-amber-900/40 text-amber-200",
    };
  }

  return {
    label: "Healthy",
    className: "border-emerald-700 bg-emerald-900/40 text-emerald-200",
  };
}

export default function InventoryProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProducts = useCallback(async () => {
    setError(null);

    try {
      const nextProducts = await inventoryApi.listProducts();
      setProducts(nextProducts);
    } catch (cause) {
      const fallback = "Unable to load the SKU catalog.";
      setError(cause instanceof InventoryApiError ? cause.message : fallback);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProducts();
  }, [loadProducts]);

  if (isLoading) {
    return <p className="text-sm text-slate-300">Loading SKU catalog...</p>;
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold">SKU catalog</h2>
        <p className="mt-1 text-sm text-slate-400">
          Current stock per SKU, client brand, and warehouse location.
        </p>
      </div>

      {error ? (
        <p className="rounded-md border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      ) : null}

      {products.length === 0 && !error ? (
        <p className="rounded-md border border-slate-800 bg-slate-900 px-3 py-4 text-sm text-slate-300">
          No SKUs are registered yet. Create products through the inventory API, then refresh
          this page.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-800">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Product</th>
                <th className="px-4 py-3 font-medium">SKU</th>
                <th className="px-4 py-3 font-medium">Client brand</th>
                <th className="px-4 py-3 font-medium">Warehouse</th>
                <th className="px-4 py-3 font-medium">Current stock</th>
                <th className="px-4 py-3 font-medium">Stock level</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => {
                const status = stockStatus(product);

                return (
                  <tr key={product.id} className="border-t border-slate-800 bg-slate-950">
                    <td className="px-4 py-3 font-medium text-slate-100">{product.name}</td>
                    <td className="px-4 py-3 font-mono text-slate-300">{product.sku}</td>
                    <td className="px-4 py-3 text-slate-300">{product.client_brand}</td>
                    <td className="px-4 py-3 text-slate-300">
                      {warehouseLabel(product.warehouse_location)}
                    </td>
                    <td className="px-4 py-3 text-slate-100">{product.current_stock}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full border px-2 py-0.5 text-xs ${status.className}`}
                      >
                        {status.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Link
                          className="rounded-md border border-emerald-700 px-2 py-1 text-xs text-emerald-200 transition hover:bg-emerald-900/40"
                          href={`/inventory/orders/inbound?productId=${product.id}`}
                        >
                          Inbound receipt
                        </Link>
                        <Link
                          className="rounded-md border border-sky-700 px-2 py-1 text-xs text-sky-200 transition hover:bg-sky-900/40"
                          href={`/inventory/orders/outbound?productId=${product.id}`}
                        >
                          Outbound pick
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
