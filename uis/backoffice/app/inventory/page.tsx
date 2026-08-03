"use client";

import { useEffect, useState } from "react";
import { flushNow, track, timedFetch } from "@/src/services/telemetry";

const API =
  process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type Product = {
  product_id: string;
  client_id: string;
  name: string;
  product_category: string;
  min_threshold: number;
};

type StockRow = {
  warehouse: string;
  product_id: string;
  client_id: string;
  product_category: string;
  quantity: number;
  min_threshold: number;
};

export default function InventoryPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [stock, setStock] = useState<StockRow[]>([]);
  const [warehouse, setWarehouse] = useState("los_angeles");
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState(5);
  const [message, setMessage] = useState("");

  async function refresh() {
    const [pRes, sRes] = await Promise.all([
      timedFetch(`${API}/inventory/products`),
      timedFetch(`${API}/inventory/stock`),
    ]);
    const p = await pRes.json();
    const s = await sRes.json();
    setProducts(p);
    setStock(s);
    if (!productId && p.length) setProductId(p[0].product_id);
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function baseProps(product: Product | undefined) {
    return {
      warehouse,
      client_id: product?.client_id || "unknown",
      product_id: productId,
      product_category: product?.product_category || "fashion",
      quantity,
    };
  }

  async function onInbound() {
    const product = products.find((p) => p.product_id === productId);
    if (!product || quantity <= 0) {
      track("inbound_order_validation_failed", {
        ...baseProps(product),
        failure_reason: "invalid_payload",
      });
      await flushNow();
      setMessage("Inbound validation failed");
      return;
    }
    const res = await timedFetch(`${API}/inventory/inbound`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ warehouse, product_id: productId, quantity }),
    });
    if (!res.ok) {
      const err = await res.json();
      track("inbound_order_validation_failed", {
        ...baseProps(product),
        failure_reason: err.detail || "api_error",
      });
      await flushNow();
      setMessage(`Inbound failed: ${err.detail}`);
      return;
    }
    const order = await res.json();
    track("inbound_order_created", {
      warehouse: order.warehouse,
      client_id: order.client_id,
      product_id: order.product_id,
      product_category: order.product_category,
      quantity: order.quantity,
      order_id: order.order_id,
    });
    await flushNow();
    setMessage(`Inbound created ${order.order_id}`);
    await refresh();
  }

  async function onOutbound() {
    const pickStarted = performance.now();
    const res = await timedFetch(`${API}/inventory/outbound`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ warehouse, product_id: productId, quantity }),
    });
    if (!res.ok) {
      const err = await res.json();
      setMessage(`Outbound failed: ${err.detail}`);
      return;
    }
    const order = await res.json();
    track("outbound_order_created", {
      warehouse: order.warehouse,
      client_id: order.client_id,
      product_id: order.product_id,
      product_category: order.product_category,
      quantity: order.quantity,
      order_id: order.order_id,
    });
    track("picking_duration_recorded", {
      warehouse: order.warehouse,
      client_id: order.client_id,
      product_id: order.product_id,
      product_category: order.product_category,
      quantity: order.quantity,
      duration_ms: Math.round(performance.now() - pickStarted),
      order_id: order.order_id,
    });
    if (order.threshold_triggered) {
      track("stock_threshold_triggered", {
        warehouse: order.warehouse,
        client_id: order.client_id,
        product_id: order.product_id,
        product_category: order.product_category,
        quantity: order.quantity,
        threshold: order.min_threshold,
        current_stock: order.current_stock,
      });
    }
    await flushNow();
    setMessage(`Outbound created ${order.order_id}`);
    await refresh();
  }

  async function onDirectEdit() {
    const res = await timedFetch(`${API}/inventory/stock/direct-edit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        warehouse,
        product_id: productId,
        attempted_delta: quantity,
      }),
    });
    const data = await res.json();
    track("direct_stock_edit_rejected", {
      warehouse: data.warehouse,
      client_id: data.client_id,
      product_id: data.product_id,
      product_category: data.product_category,
      quantity: data.quantity,
      attempted_delta: data.attempted_delta,
      reason: data.reason,
    });
    await flushNow();
    setMessage("Direct stock edit rejected (as designed)");
  }

  async function onDiscrepancy() {
    const res = await timedFetch(`${API}/inventory/discrepancy`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        warehouse,
        product_id: productId,
        counted_quantity: quantity,
      }),
    });
    if (!res.ok) {
      setMessage("Discrepancy record failed");
      return;
    }
    const data = await res.json();
    track("inventory_discrepancy_detected", {
      warehouse: data.warehouse,
      client_id: data.client_id,
      product_id: data.product_id,
      product_category: data.product_category,
      quantity: data.quantity,
      system_quantity: data.system_quantity,
      counted_quantity: data.counted_quantity,
      delta: data.delta,
    });
    await flushNow();
    setMessage(
      `Discrepancy recorded (delta ${data.delta}) for ${data.product_id}`
    );
    await refresh();
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold">Inventory operations</h1>
        <p className="mt-2 max-w-2xl text-slate-400">
          Minimal warehouse UI for emitting mandatory TrackFlow inventory
          telemetry events.
        </p>
      </header>

      <form className="grid gap-4 rounded-xl border border-slate-800 bg-slate-900 p-4 md:grid-cols-4">
        <label className="text-sm">
          Warehouse
          <select
            className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
            value={warehouse}
            onChange={(e) => setWarehouse(e.target.value)}
          >
            <option value="los_angeles">los_angeles</option>
            <option value="zaragoza">zaragoza</option>
          </select>
        </label>
        <label className="text-sm md:col-span-2">
          Product
          <select
            className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
          >
            {products.map((p) => (
              <option key={p.product_id} value={p.product_id}>
                {p.product_id} — {p.name} ({p.product_category})
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Quantity / counted
          <input
            type="number"
            className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
          />
        </label>
        <div className="flex flex-wrap gap-2 md:col-span-4">
          <button
            type="button"
            onClick={onInbound}
            className="rounded bg-emerald-600 px-3 py-2 text-sm"
          >
            Create inbound
          </button>
          <button
            type="button"
            onClick={onOutbound}
            className="rounded bg-cyan-600 px-3 py-2 text-sm"
          >
            Create outbound
          </button>
          <button
            type="button"
            onClick={onDirectEdit}
            className="rounded bg-amber-700 px-3 py-2 text-sm"
          >
            Attempt direct edit
          </button>
          <button
            type="button"
            onClick={onDiscrepancy}
            className="rounded bg-violet-700 px-3 py-2 text-sm"
          >
            Record discrepancy
          </button>
        </div>
      </form>

      {message && <p className="text-sm text-cyan-200">{message}</p>}

      <section className="overflow-hidden rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-800 text-slate-300">
            <tr>
              <th className="px-3 py-2">Warehouse</th>
              <th className="px-3 py-2">SKU</th>
              <th className="px-3 py-2">Client</th>
              <th className="px-3 py-2">Category</th>
              <th className="px-3 py-2">Qty</th>
              <th className="px-3 py-2">Min</th>
            </tr>
          </thead>
          <tbody>
            {stock.map((row) => (
              <tr
                key={`${row.warehouse}-${row.product_id}`}
                className="border-t border-slate-800"
              >
                <td className="px-3 py-2">{row.warehouse}</td>
                <td className="px-3 py-2">{row.product_id}</td>
                <td className="px-3 py-2">{row.client_id}</td>
                <td className="px-3 py-2">{row.product_category}</td>
                <td className="px-3 py-2">{row.quantity}</td>
                <td className="px-3 py-2">{row.min_threshold}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
