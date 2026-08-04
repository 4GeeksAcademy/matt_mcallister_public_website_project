"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import ProtectedShell from "@/components/ProtectedShell";
import { getToken, logout } from "@/lib/auth";
import { flushNow, timedFetch, track } from "@/src/services/telemetry";
import type {
  ProductCategory,
  Warehouse,
} from "../../../../packages/shared/types/telemetry";

const INVENTORY_API_URL = (
  process.env.NEXT_PUBLIC_INVENTORY_API_URL ?? "http://localhost:8003"
).replace(/\/$/, "");

type Product = {
  id: number;
  name: string;
  sku: string;
  warehouse_location: Warehouse;
  client_brand: string;
  low_stock_threshold: number;
  current_stock: number;
};

type Order = {
  id: number;
  order_type: "inbound" | "outbound";
  product_id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  created_at: string;
  user_uuid: string;
};

type ProductDraft = {
  name: string;
  sku: string;
  warehouse_location: Warehouse;
  client_brand: string;
  low_stock_threshold: number;
};

const initialProduct: ProductDraft = {
  name: "",
  sku: "",
  warehouse_location: "los_angeles",
  client_brand: "",
  low_stock_threshold: 10,
};

const DEFAULT_CATEGORY: ProductCategory = "fashion";

function telemetryProps(product: Product | undefined, quantity: number) {
  return {
    warehouse: product?.warehouse_location ?? "los_angeles",
    client_id: product?.client_brand || "unknown",
    product_id: product ? String(product.id) : "unknown",
    product_category: DEFAULT_CATEGORY,
    quantity,
  };
}

async function inventoryRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  if (!token) {
    logout();
    throw new Error("You need to sign in to continue.");
  }

  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (options.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await timedFetch(`${INVENTORY_API_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });
  if (response.status === 401) {
    logout();
    throw new Error("Your session has expired.");
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "Inventory request failed.");
  }
  return response.json() as Promise<T>;
}

function InventoryContent() {
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [productDraft, setProductDraft] = useState<ProductDraft>(initialProduct);
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [nextProducts, nextOrders] = await Promise.all([
        inventoryRequest<Product[]>("/inventory/products"),
        inventoryRequest<Order[]>("/inventory/orders"),
      ]);
      setProducts(nextProducts);
      setOrders(nextOrders);
      setProductId((current) => {
        if (current) return current;
        return nextProducts.length > 0 ? String(nextProducts[0].id) : current;
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load inventory.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void refresh(), 0);
    return () => window.clearTimeout(timeout);
  }, [refresh]);

  async function createProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setMessage("");
    try {
      await inventoryRequest<Product>("/inventory/products", {
        method: "POST",
        body: JSON.stringify(productDraft),
      });
      setProductDraft(initialProduct);
      setMessage("Product created.");
      await refresh();
      await flushNow();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to create product.");
    } finally {
      setSubmitting(false);
    }
  }

  async function createOrder(orderType: Order["order_type"]) {
    if (!productId || quantity <= 0) {
      setError("Select a product and enter a positive quantity.");
      return;
    }

    const product = products.find((item) => String(item.id) === productId);
    const props = telemetryProps(product, quantity);
    setSubmitting(true);
    setError("");
    setMessage("");
    const started = performance.now();

    try {
      const created = await inventoryRequest<{ id: number }>(
        `/inventory/orders/${orderType}`,
        {
          method: "POST",
          body: JSON.stringify({ product_id: Number(productId), quantity }),
        },
      );

      if (orderType === "inbound") {
        track("inbound_order_created", {
          ...props,
          order_id: String(created.id),
        });
      } else {
        track("outbound_order_created", {
          ...props,
          order_id: String(created.id),
        });
        track("picking_duration_recorded", {
          ...props,
          order_id: String(created.id),
          duration_ms: Math.round(performance.now() - started),
        });

        const nextStock = (product?.current_stock ?? 0) - quantity;
        const threshold = product?.low_stock_threshold ?? 0;
        if (nextStock <= threshold) {
          track("stock_threshold_triggered", {
            ...props,
            quantity: nextStock,
            threshold,
            current_stock: Math.max(0, nextStock),
          });
        }
      }

      setMessage(`${orderType === "inbound" ? "Inbound" : "Outbound"} order created.`);
      await refresh();
      await flushNow();
    } catch (cause) {
      const failure =
        cause instanceof Error ? cause.message : "Unable to create order.";
      if (orderType === "inbound") {
        track("inbound_order_validation_failed", {
          ...props,
          failure_reason: failure.slice(0, 120),
        });
      } else {
        track("outbound_order_rejected", {
          ...props,
          failure_reason: failure.slice(0, 120),
        });
      }
      setError(failure);
      await flushNow();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold">Inventory operations</h1>
        <p className="mt-2 text-slate-400">
          Manage warehouse products and authenticated inbound and outbound orders.
          Mutations emit TrackFlow telemetry events.
        </p>
      </header>

      {error ? (
        <p className="rounded border border-red-800 bg-red-900/20 px-4 py-3 text-red-200">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="rounded border border-emerald-800 bg-emerald-900/20 px-4 py-3 text-emerald-200">
          {message}
        </p>
      ) : null}

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h2 className="text-xl font-semibold">Add product</h2>
        <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={createProduct}>
          <input
            className="rounded border border-slate-700 bg-slate-950 px-3 py-2"
            onChange={(event) =>
              setProductDraft((current) => ({ ...current, name: event.target.value }))
            }
            placeholder="Product name"
            required
            value={productDraft.name}
          />
          <input
            className="rounded border border-slate-700 bg-slate-950 px-3 py-2"
            onChange={(event) =>
              setProductDraft((current) => ({ ...current, sku: event.target.value }))
            }
            placeholder="SKU"
            required
            value={productDraft.sku}
          />
          <input
            className="rounded border border-slate-700 bg-slate-950 px-3 py-2"
            onChange={(event) =>
              setProductDraft((current) => ({
                ...current,
                client_brand: event.target.value,
              }))
            }
            placeholder="Client brand"
            required
            value={productDraft.client_brand}
          />
          <select
            className="rounded border border-slate-700 bg-slate-950 px-3 py-2"
            onChange={(event) =>
              setProductDraft((current) => ({
                ...current,
                warehouse_location: event.target.value as Warehouse,
              }))
            }
            value={productDraft.warehouse_location}
          >
            <option value="los_angeles">Los Angeles</option>
            <option value="zaragoza">Zaragoza</option>
          </select>
          <label className="text-sm text-slate-300">
            Low-stock threshold
            <input
              className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
              min={0}
              onChange={(event) =>
                setProductDraft((current) => ({
                  ...current,
                  low_stock_threshold: Number(event.target.value),
                }))
              }
              type="number"
              value={productDraft.low_stock_threshold}
            />
          </label>
          <button
            className="self-end rounded bg-cyan-500 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60"
            disabled={submitting}
            type="submit"
          >
            Create product
          </button>
        </form>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h2 className="text-xl font-semibold">Create order</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <select
            className="rounded border border-slate-700 bg-slate-950 px-3 py-2 md:col-span-2"
            onChange={(event) => setProductId(event.target.value)}
            value={productId}
          >
            <option value="">Select a product</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.sku} — {product.name} ({product.current_stock} available)
              </option>
            ))}
          </select>
          <input
            className="rounded border border-slate-700 bg-slate-950 px-3 py-2"
            min={1}
            onChange={(event) => setQuantity(Number(event.target.value))}
            type="number"
            value={quantity}
          />
          <div className="flex gap-2">
            <button
              className="rounded bg-emerald-600 px-3 py-2 text-sm disabled:opacity-60"
              disabled={submitting}
              onClick={() => void createOrder("inbound")}
              type="button"
            >
              Inbound
            </button>
            <button
              className="rounded bg-cyan-600 px-3 py-2 text-sm disabled:opacity-60"
              disabled={submitting}
              onClick={() => void createOrder("outbound")}
              type="button"
            >
              Outbound
            </button>
          </div>
        </div>
      </section>

      <section className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-800 text-slate-300">
            <tr>
              <th className="px-3 py-2">SKU</th>
              <th className="px-3 py-2">Product</th>
              <th className="px-3 py-2">Warehouse</th>
              <th className="px-3 py-2">Brand</th>
              <th className="px-3 py-2">Stock</th>
              <th className="px-3 py-2">Threshold</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="px-3 py-3 text-slate-400" colSpan={6}>
                  Loading inventory...
                </td>
              </tr>
            ) : (
              products.map((product) => (
                <tr className="border-t border-slate-800" key={product.id}>
                  <td className="px-3 py-2">{product.sku}</td>
                  <td className="px-3 py-2">{product.name}</td>
                  <td className="px-3 py-2">{product.warehouse_location}</td>
                  <td className="px-3 py-2">{product.client_brand}</td>
                  <td className="px-3 py-2">{product.current_stock}</td>
                  <td className="px-3 py-2">{product.low_stock_threshold}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="overflow-x-auto rounded-xl border border-slate-800">
        <h2 className="bg-slate-900 px-4 py-3 text-xl font-semibold">Recent orders</h2>
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-800 text-slate-300">
            <tr>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">SKU</th>
              <th className="px-3 py-2">Quantity</th>
              <th className="px-3 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr className="border-t border-slate-800" key={`${order.order_type}-${order.id}`}>
                <td className="px-3 py-2 capitalize">{order.order_type}</td>
                <td className="px-3 py-2">{order.product_sku}</td>
                <td className="px-3 py-2">{order.quantity}</td>
                <td className="px-3 py-2">{new Date(order.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}

export default function InventoryPage() {
  return (
    <ProtectedShell>
      <InventoryContent />
    </ProtectedShell>
  );
}
