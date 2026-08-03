"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type SupplierStatus = "active" | "suspended";
type SupplierCountry = "USA" | "Spain";
type SupplierCurrency = "USD" | "EUR";

type Supplier = {
  id: number;
  name: string;
  country: SupplierCountry;
  categories: string[];
  rate_per_shipment: number;
  currency: SupplierCurrency;
  rate_updated_at: string;
  status: SupplierStatus;
  service_zone?: string | null;
  contact_email?: string | null;
  notes?: string | null;
};

type CreateSupplierPayload = Omit<Supplier, "id" | "rate_updated_at">;

const VALID_CATEGORIES = [
  "carrier_last_mile",
  "carrier_international",
  "warehouse_supplies",
  "packaging_materials",
  "reverse_logistics",
  "fleet_maintenance",
  "it_and_wms_software",
  "cleaning_and_facilities",
] as const;

const API_BASE_URL = "/api";

const emptyForm: CreateSupplierPayload = {
  name: "",
  country: "USA",
  categories: ["carrier_last_mile"],
  rate_per_shipment: 1,
  currency: "USD",
  status: "active",
  service_zone: "",
  contact_email: "",
  notes: "",
};

function statusBadgeClass(status: SupplierStatus): string {
  if (status === "active") {
    return "bg-emerald-900/40 text-emerald-300 border-emerald-700";
  }

  return "bg-amber-900/40 text-amber-300 border-amber-700";
}

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [countryFilter, setCountryFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [form, setForm] = useState<CreateSupplierPayload>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [rateDrafts, setRateDrafts] = useState<Record<number, string>>({});

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (countryFilter) {
      params.set("country", countryFilter);
    }
    if (categoryFilter) {
      params.set("category", categoryFilter);
    }
    return params.toString();
  }, [categoryFilter, countryFilter]);

  const fetchSuppliers = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError("");

    try {
      const url = queryString
        ? `${API_BASE_URL}/suppliers?${queryString}`
        : `${API_BASE_URL}/suppliers`;
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load suppliers");
      }
      const data = (await response.json()) as Supplier[];
      setSuppliers(data);

      const nextDrafts: Record<number, string> = {};
      for (const supplier of data) {
        nextDrafts[supplier.id] = String(supplier.rate_per_shipment);
      }
      setRateDrafts(nextDrafts);
    } catch {
      setError("Could not load supplier data. Ensure the API is running.");
    } finally {
      setLoading(false);
    }
  }, [queryString]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      void fetchSuppliers();
    }, 0);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [fetchSuppliers]);

  function onCountryChange(value: SupplierCountry) {
    setForm((current) => ({
      ...current,
      country: value,
      currency: value === "USA" ? "USD" : "EUR",
    }));
  }

  async function submitSupplier(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const payload: CreateSupplierPayload = {
        ...form,
        service_zone: form.service_zone?.trim() || undefined,
        contact_email: form.contact_email?.trim() || undefined,
        notes: form.notes?.trim() || undefined,
      };

      const response = await fetch(`${API_BASE_URL}/suppliers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        if (response.status === 422) {
          throw new Error("Validation failed. Check supplier data and try again.");
        }
        throw new Error("Could not create supplier.");
      }

      setForm(emptyForm);
      await fetchSuppliers();
    } catch (cause) {
      const nextError =
        cause instanceof Error ? cause.message : "Could not create supplier.";
      setError(nextError);
    } finally {
      setSaving(false);
    }
  }

  async function updateRate(supplierId: number): Promise<void> {
    setError("");
    const value = Number(rateDrafts[supplierId]);

    if (!Number.isFinite(value) || value <= 0) {
      setError("Rate must be a number greater than zero.");
      return;
    }

    const response = await fetch(`${API_BASE_URL}/suppliers/${supplierId}/rate`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rate_per_shipment: value }),
    });

    if (!response.ok) {
      setError("Failed to update rate.");
      return;
    }

    await fetchSuppliers();
  }

  async function toggleStatus(supplier: Supplier): Promise<void> {
    setError("");
    const nextStatus: SupplierStatus =
      supplier.status === "active" ? "suspended" : "active";

    const response = await fetch(`${API_BASE_URL}/suppliers/${supplier.id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: nextStatus }),
    });

    if (!response.ok) {
      setError("Failed to update supplier status.");
      return;
    }

    await fetchSuppliers();
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-10 md:px-10">
        <header className="space-y-3">
          <nav className="flex gap-3 text-sm text-cyan-300">
            <Link className="underline-offset-4 hover:underline" href="/">
              Dashboard
            </Link>
            <Link className="underline underline-offset-4" href="/suppliers">
              Suppliers
            </Link>
          </nav>
          <h1 className="text-3xl font-semibold md:text-4xl">Supplier Directory</h1>
          <p className="max-w-2xl text-slate-300">
            Manage supplier contracts for USA and Spain with fast filtering,
            registration, rate updates, and status controls.
          </p>
        </header>

        {error ? (
          <p className="rounded-lg border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-300">
            {error}
          </p>
        ) : null}

        <section className="grid grid-cols-1 gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 md:grid-cols-3">
          <label className="flex flex-col gap-2 text-sm text-slate-300">
            Country filter
            <select
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              value={countryFilter}
              onChange={(event) => setCountryFilter(event.target.value)}
            >
              <option value="">All countries</option>
              <option value="USA">USA</option>
              <option value="Spain">Spain</option>
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm text-slate-300">
            Category filter
            <select
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              value={categoryFilter}
              onChange={(event) => setCategoryFilter(event.target.value)}
            >
              <option value="">All categories</option>
              {VALID_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <button
            className="self-end rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700"
            onClick={() => {
              setCountryFilter("");
              setCategoryFilter("");
            }}
            type="button"
          >
            Clear filters
          </button>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="mb-4 text-xl font-medium">Register Supplier</h2>
          <form className="grid grid-cols-1 gap-3 md:grid-cols-2" onSubmit={submitSupplier}>
            <input
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              placeholder="Supplier name"
              required
              value={form.name}
              onChange={(event) =>
                setForm((current) => ({ ...current, name: event.target.value }))
              }
            />
            <select
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.country}
              onChange={(event) => onCountryChange(event.target.value as SupplierCountry)}
            >
              <option value="USA">USA</option>
              <option value="Spain">Spain</option>
            </select>
            <select
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.currency}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  currency: event.target.value as SupplierCurrency,
                }))
              }
            >
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </select>
            <select
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.status}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  status: event.target.value as SupplierStatus,
                }))
              }
            >
              <option value="active">active</option>
              <option value="suspended">suspended</option>
            </select>
            <select
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.categories[0]}
              onChange={(event) =>
                setForm((current) => ({ ...current, categories: [event.target.value] }))
              }
            >
              {VALID_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
            <input
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              min={0.01}
              placeholder="Rate per shipment"
              required
              step="0.01"
              type="number"
              value={form.rate_per_shipment}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  rate_per_shipment: Number(event.target.value),
                }))
              }
            />
            <input
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              placeholder="Service zone (optional)"
              value={form.service_zone ?? ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, service_zone: event.target.value }))
              }
            />
            <input
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
              placeholder="Contact email (optional)"
              type="email"
              value={form.contact_email ?? ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, contact_email: event.target.value }))
              }
            />
            <textarea
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 md:col-span-2"
              placeholder="Notes (optional)"
              rows={2}
              value={form.notes ?? ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, notes: event.target.value }))
              }
            />
            <button
              className="rounded-lg bg-cyan-600 px-4 py-2 font-medium text-slate-950 hover:bg-cyan-500 md:col-span-2"
              disabled={saving}
              type="submit"
            >
              {saving ? "Creating..." : "Create Supplier"}
            </button>
          </form>
        </section>

        <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800 text-slate-300">
              <tr>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Country</th>
                <th className="px-4 py-3 font-medium">Categories</th>
                <th className="px-4 py-3 font-medium">Rate</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td className="px-4 py-4 text-slate-400" colSpan={6}>
                    Loading suppliers...
                  </td>
                </tr>
              ) : suppliers.length === 0 ? (
                <tr>
                  <td className="px-4 py-4 text-slate-400" colSpan={6}>
                    No suppliers found.
                  </td>
                </tr>
              ) : (
                suppliers.map((supplier) => (
                  <tr className="border-t border-slate-800" key={supplier.id}>
                    <td className="px-4 py-3">{supplier.name}</td>
                    <td className="px-4 py-3">{supplier.country}</td>
                    <td className="px-4 py-3">{supplier.categories.join(", ")}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <input
                          className="w-24 rounded border border-slate-700 bg-slate-950 px-2 py-1"
                          min={0.01}
                          step="0.01"
                          type="number"
                          value={rateDrafts[supplier.id] ?? String(supplier.rate_per_shipment)}
                          onChange={(event) =>
                            setRateDrafts((current) => ({
                              ...current,
                              [supplier.id]: event.target.value,
                            }))
                          }
                        />
                        <span>{supplier.currency}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full border px-2 py-1 text-xs font-medium ${statusBadgeClass(
                          supplier.status,
                        )}`}
                      >
                        {supplier.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          className="rounded border border-slate-700 px-3 py-1 hover:bg-slate-800"
                          onClick={() => {
                            void updateRate(supplier.id);
                          }}
                          type="button"
                        >
                          Update rate
                        </button>
                        <button
                          className="rounded border border-slate-700 px-3 py-1 hover:bg-slate-800"
                          onClick={() => {
                            void toggleStatus(supplier);
                          }}
                          type="button"
                        >
                          {supplier.status === "active" ? "Suspend" : "Activate"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}
