"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  asIncident,
  asIncidentList,
  branchLabel,
  getFriendlyError,
  incidentBranches,
  incidentCategories,
  incidentOrigins,
  incidentStatuses,
} from "@/components/incidentDomain";
import { Incident } from "../../../../packages/shared/types";

type Filters = {
  status: string;
  category: string;
  origin: string;
  branch: string;
};

const initialFilters: Filters = {
  status: "",
  category: "",
  origin: "",
  branch: "",
};

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();

    if (filters.status) params.set("status", filters.status);
    if (filters.category) params.set("category", filters.category);
    if (filters.origin) params.set("origin", filters.origin);
    if (filters.branch) params.set("branch", filters.branch);

    const query = params.toString();
    return query ? `?${query}` : "";
  }, [filters]);

  const loadIncidents = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/incidents${queryString}`, { cache: "no-store" });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(getFriendlyError(payload, "Unable to load incidents right now."));
      }

      setIncidents(asIncidentList(payload));
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Unable to load incidents right now.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [queryString]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadIncidents(), 0);
    return () => window.clearTimeout(timeout);
  }, [loadIncidents]);

  const onStatusChange = async (incident: Incident, nextStatus: string) => {
    const previous = incident.status;

    if (previous === nextStatus) {
      return;
    }

    setUpdatingId(incident.id);
    setError(null);

    setIncidents((prev) =>
      prev.map((item) =>
        item.id === incident.id
          ? { ...item, status: nextStatus as Incident["status"] }
          : item,
      ),
    );

    try {
      const response = await fetch(`/api/incidents/${incident.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(getFriendlyError(payload, "Could not update incident status."));
      }

      const updated = asIncident(payload);

      if (!updated) {
        throw new Error("Could not update incident status.");
      }

      setIncidents((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch {
      setIncidents((prev) =>
        prev.map((item) =>
          item.id === incident.id ? { ...item, status: previous } : item,
        ),
      );
      setError("Could not update incident status. Changes were reverted.");
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10 text-slate-100 md:px-10">
      <header className="mb-6">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Incident Manager</p>
        <h1 className="mt-2 text-3xl font-semibold">Incidents</h1>
      </header>

      <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <select
            aria-label="Filter by status"
            value={filters.status}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, status: event.target.value }))
            }
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          >
            <option value="">All statuses</option>
            {incidentStatuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>

          <select
            aria-label="Filter by category"
            value={filters.category}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, category: event.target.value }))
            }
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          >
            <option value="">All categories</option>
            {incidentCategories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>

          <select
            aria-label="Filter by origin"
            value={filters.origin}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, origin: event.target.value }))
            }
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          >
            <option value="">All origins</option>
            {incidentOrigins.map((origin) => (
              <option key={origin} value={origin}>
                {origin}
              </option>
            ))}
          </select>

          <select
            aria-label="Filter by branch"
            value={filters.branch}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, branch: event.target.value }))
            }
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          >
            <option value="">All branches</option>
            {incidentBranches.map((branch) => (
              <option key={branch} value={branch}>
                {branchLabel(branch)}
              </option>
            ))}
          </select>
        </div>
      </section>

      {error ? (
        <div className="mb-4 rounded-md border border-red-300 bg-red-900/30 px-4 py-3 text-sm text-red-100">
          <p>{error}</p>
          <button
            onClick={() => void loadIncidents()}
            className="mt-2 rounded-md border border-red-200 px-3 py-1"
          >
            Retry
          </button>
        </div>
      ) : null}

      {isLoading ? (
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
          Loading incidents...
        </section>
      ) : incidents.length === 0 ? (
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
          No incidents found for the current filters.
        </section>
      ) : (
        <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800 text-slate-300">
              <tr>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Origin</th>
                <th className="px-4 py-3 font-medium">Branch</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((incident) => (
                <tr key={incident.id} className="border-t border-slate-800">
                  <td className="px-4 py-3">{incident.title}</td>
                  <td className="px-4 py-3">{incident.category}</td>
                  <td className="px-4 py-3">{incident.origin}</td>
                  <td className="px-4 py-3">{branchLabel(incident.branch)}</td>
                  <td className="px-4 py-3">
                    <select
                      value={incident.status}
                      disabled={updatingId === incident.id}
                      onChange={(event) =>
                        void onStatusChange(incident, event.target.value)
                      }
                      className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1"
                    >
                      {incidentStatuses.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}
