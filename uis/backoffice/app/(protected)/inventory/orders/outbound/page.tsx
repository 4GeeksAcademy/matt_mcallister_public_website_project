"use client";

import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import {
  InventoryApiError,
  inventoryApi,
  warehouseLabel,
  type Product,
} from "@/lib/inventory";

function OutboundOrderForm() {
  const searchParams = useSearchParams();
  const preselectedId = searchParams.get("productId") ?? "";

  const [products, setProducts] = useState<Product[]>([]);
  const [productId, setProductId] = useState(preselectedId);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isStockLoading, setIsStockLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [quantityError, setQuantityError] = useState<string | null>(null);

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
        const fallback = "Unable to load SKUs for outbound pick.";
        setError(cause instanceof InventoryApiError ? cause.message : fallback);
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [preselectedId]);

  useEffect(() => {
    if (!productId) {
      setSelectedProduct(null);
      return;
    }

    let cancelled = false;

    const loadStock = async () => {
      setIsStockLoading(true);
      setQuantityError(null);

      try {
        const product = await inventoryApi.getProduct(Number(productId));
        if (!cancelled) {
          setSelectedProduct(product);
        }
      } catch (cause) {
        if (!cancelled) {
          setSelectedProduct(null);
          const fallback = "Unable to load current stock for the selected SKU.";
          setError(cause instanceof InventoryApiError ? cause.message : fallback);
        }
      } finally {
        if (!cancelled) {
          setIsStockLoading(false);
        }
      }
    };

    void loadStock();

    return () => {
      cancelled = true;
    };
  }, [productId]);

  const exceedsStock = useMemo(() => {
    if (!selectedProduct) {
      return false;
    }

    return quantity > selectedProduct.current_stock;
  }, [quantity, selectedProduct]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setQuantityError(null);

    if (selectedProduct && quantity > selectedProduct.current_stock) {
      setQuantityError(
        `Quantity exceeds available stock (${selectedProduct.current_stock}). Reduce the pick quantity before submitting.`
      );
      return;
    }

    setIsSubmitting(true);

    try {
      await inventoryApi.createOutboundOrder({
        product_id: Number(productId),
        quantity,
      });
      setQuantity(1);
      setMessage(
        selectedProduct
          ? `Outbound pick recorded for ${selectedProduct.name} (${selectedProduct.sku}).`
          : "Outbound pick recorded."
      );

      const refreshed = await inventoryApi.getProduct(Number(productId));
      setSelectedProduct(refreshed);
    } catch (cause) {
      const fallback = "Unable to record the outbound pick.";
      const apiMessage = cause instanceof InventoryApiError ? cause.message : fallback;

      if (cause instanceof InventoryApiError && cause.status === 400) {
        setQuantityError(apiMessage);
      } else {
        setError(apiMessage);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <p className="text-sm text-slate-300">Loading outbound pick form...</p>;
  }

  return (
    <section className="max-w-xl space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Outbound pick</h2>
        <p className="mt-1 text-sm text-slate-400">
          Deduct stock leaving the warehouse. Current stock is loaded when you select a SKU,
          before you enter a quantity.
        </p>
      </div>

      <form
        className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-5"
        onSubmit={handleSubmit}
      >
        <div>
          <label className="mb-1 block text-sm" htmlFor="outbound-product">
            SKU / product
          </label>
          <select
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            id="outbound-product"
            onChange={(event) => {
              setProductId(event.target.value);
              setMessage(null);
              setError(null);
              setQuantityError(null);
            }}
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

        <div className="rounded-md border border-slate-700 bg-slate-950 px-3 py-3 text-sm">
          <p className="text-slate-400">Current stock</p>
          {isStockLoading ? (
            <p className="mt-1 text-slate-200">Loading stock...</p>
          ) : selectedProduct ? (
            <p className="mt-1 text-lg font-semibold text-slate-100">
              {selectedProduct.current_stock}{" "}
              <span className="text-sm font-normal text-slate-400">
                units at {warehouseLabel(selectedProduct.warehouse_location)}
              </span>
            </p>
          ) : (
            <p className="mt-1 text-slate-300">Select a SKU to see available stock.</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-sm" htmlFor="outbound-quantity">
            Quantity to pick
          </label>
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            id="outbound-quantity"
            min={1}
            onChange={(event) => {
              setQuantity(Number(event.target.value));
              setQuantityError(null);
            }}
            required
            type="number"
            value={quantity}
          />
          {exceedsStock ? (
            <p className="mt-2 text-sm text-amber-200">
              Quantity exceeds available stock ({selectedProduct?.current_stock}). Reduce the
              pick quantity before submitting.
            </p>
          ) : null}
          {quantityError ? (
            <p className="mt-2 rounded-md border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-200">
              {quantityError}
            </p>
          ) : null}
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
          disabled={isSubmitting || products.length === 0 || exceedsStock}
          type="submit"
        >
          {isSubmitting ? "Recording..." : "Record outbound pick"}
        </button>
      </form>
    </section>
  );
}

export default function OutboundOrderPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-300">Loading outbound pick form...</p>}>
      <OutboundOrderForm />
    </Suspense>
  );
}
