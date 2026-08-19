"use client";

import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import {
  InventoryApiError,
  inventoryApi,
  warehouseLabel,
  type Product,
} from "@/lib/inventory";

function InboundOrderForm() {
  const searchParams = useSearchParams();
  const preselectedId = searchParams.get("productId") ?? "";

  const [products, setProducts] = useState<Product[]>([]);
  const [productId, setProductId] = useState(preselectedId);
  const [quantity, setQuantity] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const nextProducts = await inventoryApi.listProducts();
        setProducts(nextProducts);
        setProductId((current) => {
          if (current) {
            return current;
          }

          return preselectedId || (nextProducts[0] ? String(nextProducts[0].id) : "");
        });
      } catch (cause) {
        const fallback = "Unable to load SKUs for inbound receipt.";
        setError(cause instanceof InventoryApiError ? cause.message : fallback);
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [preselectedId]);

  const selectedProduct = useMemo(
    () => products.find((product) => String(product.id) === productId),
    [products, productId]
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSubmitting(true);

    try {
      await inventoryApi.createInboundOrder({
        product_id: Number(productId),
        quantity,
      });
      setQuantity(1);
      setMessage(
        selectedProduct
          ? `Inbound receipt recorded for ${selectedProduct.name} (${selectedProduct.sku}).`
          : "Inbound receipt recorded."
      );
    } catch (cause) {
      const fallback = "Unable to record the inbound receipt.";
      setError(cause instanceof InventoryApiError ? cause.message : fallback);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <p className="text-sm text-slate-300">Loading inbound receipt form...</p>;
  }

  return (
    <section className="max-w-xl space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Inbound receipt</h2>
        <p className="mt-1 text-sm text-slate-400">
          Record stock arriving into a warehouse. Select the SKU by name — do not type a raw ID.
        </p>
      </div>

      <form
        className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-5"
        onSubmit={handleSubmit}
      >
        <div>
          <label className="mb-1 block text-sm" htmlFor="inbound-product">
            SKU / product
          </label>
          <select
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            id="inbound-product"
            onChange={(event) => setProductId(event.target.value)}
            required
            value={productId}
          >
            {products.length === 0 ? (
              <option value="">No SKUs available</option>
            ) : (
              products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name} ({product.sku}) — {warehouseLabel(product.warehouse_location)}
                </option>
              ))
            )}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm" htmlFor="inbound-quantity">
            Quantity received
          </label>
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            id="inbound-quantity"
            min={1}
            onChange={(event) => setQuantity(Number(event.target.value))}
            required
            type="number"
            value={quantity}
          />
        </div>

        {message ? (
          <p className="rounded-md border border-green-700 bg-green-900/30 px-3 py-2 text-sm text-green-200">
            {message}
          </p>
        ) : null}

        {error ? (
          <p className="rounded-md border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-200">
            {error}
          </p>
        ) : null}

        <button
          className="rounded-md bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-70"
          disabled={isSubmitting || products.length === 0}
          type="submit"
        >
          {isSubmitting ? "Recording..." : "Record inbound receipt"}
        </button>
      </form>
    </section>
  );
}

export default function InboundOrderPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-300">Loading inbound receipt form...</p>}>
      <InboundOrderForm />
    </Suspense>
  );
}
