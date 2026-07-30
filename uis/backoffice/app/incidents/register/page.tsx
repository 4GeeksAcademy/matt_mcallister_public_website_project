"use client";

import { FormEvent, useMemo, useState } from "react";
import {
  ApiFieldError,
  branchLabel,
  incidentBranches,
  incidentCategories,
  incidentOrigins,
  incidentStatuses,
} from "@/components/incidentDomain";

type FormData = {
  title: string;
  description: string;
  category: string;
  status: string;
  origin: string;
  branch: string;
};

const initialData: FormData = {
  title: "",
  description: "",
  category: incidentCategories[0],
  status: "open",
  origin: incidentOrigins[0],
  branch: incidentBranches[0],
};

export default function RegisterIncidentPage() {
  const [data, setData] = useState<FormData>(initialData);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const branchHighlightClass = useMemo(() => {
    if (data.origin === "branch") {
      return "ring-2 ring-cyan-400/60 border-cyan-300";
    }

    return "border-slate-700";
  }, [data.origin]);

  const onFieldChange = (field: keyof FormData, value: string) => {
    setData((prev) => ({ ...prev, [field]: value }));
    setStatusMessage(null);
    setErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setStatusMessage(null);
    setErrors({});

    const clientErrors: Record<string, string> = {};
    if (!data.title.trim()) clientErrors.title = "Title is required.";
    if (!data.description.trim()) clientErrors.description = "Description is required.";
    if (!data.category.trim()) clientErrors.category = "Category is required.";
    if (!data.status.trim()) clientErrors.status = "Status is required.";
    if (!data.origin.trim()) clientErrors.origin = "Origin is required.";
    if (!data.branch.trim()) clientErrors.branch = "Branch is required.";

    if (Object.keys(clientErrors).length > 0) {
      setErrors(clientErrors);
      setStatusMessage({
        kind: "error",
        message: "Please complete the required fields before submitting.",
      });
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await fetch("/api/incidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const payload = (await response.json()) as {
        message?: string;
        error?: ApiFieldError;
      };

      if (!response.ok) {
        const fieldError = payload.error;

        if (fieldError?.field) {
          setErrors((prev) => ({ ...prev, [fieldError.field]: fieldError.message }));
        }

        setStatusMessage({
          kind: "error",
          message: "We could not save the incident. Please review the highlighted fields.",
        });
        return;
      }

      setData(initialData);
      setStatusMessage({
        kind: "success",
        message: "Incident registered successfully.",
      });
    } catch {
      setStatusMessage({
        kind: "error",
        message: "The service is temporarily unavailable. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto w-full max-w-4xl px-6 py-10 text-slate-100 md:px-10">
      <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Incident Manager</p>
        <h1 className="mt-2 text-3xl font-semibold">Register Incident</h1>
        <p className="mt-2 text-slate-300">Log incidents from branches, customer reports, or internal detection.</p>
      </header>

      <form onSubmit={onSubmit} className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        {statusMessage ? (
          <div
            role="status"
            className={`rounded-md border px-4 py-3 text-sm ${
              statusMessage.kind === "success"
                ? "border-green-300 bg-green-900/30 text-green-100"
                : "border-red-300 bg-red-900/30 text-red-100"
            }`}
          >
            {statusMessage.message}
          </div>
        ) : null}

        <div>
          <label className="mb-2 block text-sm font-medium" htmlFor="title">
            Title
          </label>
          <input
            id="title"
            value={data.title}
            onChange={(event) => onFieldChange("title", event.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          />
          {errors.title ? <p className="mt-1 text-sm text-red-300">{errors.title}</p> : null}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium" htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            rows={4}
            value={data.description}
            onChange={(event) => onFieldChange("description", event.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          />
          {errors.description ? <p className="mt-1 text-sm text-red-300">{errors.description}</p> : null}
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="category">
              Category
            </label>
            <select
              id="category"
              value={data.category}
              onChange={(event) => onFieldChange("category", event.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            >
              {incidentCategories.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.category ? <p className="mt-1 text-sm text-red-300">{errors.category}</p> : null}
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="status">
              Status
            </label>
            <select
              id="status"
              value={data.status}
              onChange={(event) => onFieldChange("status", event.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            >
              {incidentStatuses.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.status ? <p className="mt-1 text-sm text-red-300">{errors.status}</p> : null}
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="origin">
              Origin
            </label>
            <select
              id="origin"
              value={data.origin}
              onChange={(event) => onFieldChange("origin", event.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            >
              {incidentOrigins.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.origin ? <p className="mt-1 text-sm text-red-300">{errors.origin}</p> : null}
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="branch">
              Branch
            </label>
            <select
              id="branch"
              value={data.branch}
              onChange={(event) => onFieldChange("branch", event.target.value)}
              className={`w-full rounded-md border bg-slate-950 px-3 py-2 ${branchHighlightClass}`}
            >
              {incidentBranches.map((option) => (
                <option key={option} value={option}>
                  {branchLabel(option)}
                </option>
              ))}
            </select>
            {errors.branch ? <p className="mt-1 text-sm text-red-300">{errors.branch}</p> : null}
            {data.origin === "branch" ? (
              <p className="mt-1 text-xs text-cyan-200">Branch origin selected: choose the specific reporting location.</p>
            ) : null}
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex items-center rounded-md border border-cyan-300 bg-cyan-500/20 px-4 py-2 text-sm font-semibold text-cyan-100 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Saving..." : "Register incident"}
        </button>
      </form>
    </main>
  );
}
