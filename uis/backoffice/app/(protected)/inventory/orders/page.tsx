"use client";

import { useCallback, useEffect, useState } from "react";

import { InventoryApiError, inventoryApi, type Order } from "@/lib/inventory";

function formatDate(value: string) {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

function orderTypeStyles(orderType: Order["order_type"]) {
  if (orderType === "inbound") {
    return {
      label: "Inbound receipt",
      className: "border-emerald-700 bg-emerald-900/40 text-emerald-200",
    };
  }

  return {
    label: "Outbound pick",
    className: "border-sky-700 bg-sky-900/40 text-sky-200",
  };
}

export default function InventoryOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOrders = useCallback(async () => {
    setError(null);

    try {
      const nextOrders = await inventoryApi.listOrders();
      setOrders(nextOrders);
    } catch (cause) {
      const fallback = "Unable to load stock movement history.";
      setError(cause instanceof InventoryApiError ? cause.message : fallback);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadOrders();
  }, [loadOrders]);

  if (isLoading) {
    return <p className="text-sm text-slate-300">Loading stock movements...</p>;
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Stock movements</h2>
        <p className="mt-1 text-sm text-slate-400">
          Read-only history of inbound receipts and outbound picks, including the operator
          user_uuid.
        </p>
      </div>

      {error ? (
        <p className="rounded-md border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      ) : null}

      {orders.length === 0 && !error ? (
        <p className="rounded-md border border-slate-800 bg-slate-900 px-3 py-4 text-sm text-slate-300">
          No inbound receipts or outbound picks have been recorded yet.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-800">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Movement</th>
                <th className="px-4 py-3 font-medium">Product</th>
                <th className="px-4 py-3 font-medium">Quantity</th>
                <th className="px-4 py-3 font-medium">Created</th>
                <th className="px-4 py-3 font-medium">user_uuid</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const type = orderTypeStyles(order.order_type);

                return (
                  <tr key={order.id} className="border-t border-slate-800 bg-slate-950">
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full border px-2 py-0.5 text-xs ${type.className}`}
                      >
                        {type.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-100">{order.product_name}</p>
                      <p className="font-mono text-xs text-slate-400">{order.product_sku}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-100">{order.quantity}</td>
                    <td className="px-4 py-3 text-slate-300">{formatDate(order.created_at)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-300">
                      {order.user_uuid}
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
