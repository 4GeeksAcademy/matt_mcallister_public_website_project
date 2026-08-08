"use client";

import { FormEvent, useState } from "react";

import { incidentsUrl } from "@/lib/apiBase";

type TicketProgress = {
  ticket_id: string;
  status: string;
  departments: Record<string, { status?: string; iteration?: number }>;
  evaluations: Record<string, { overall_pass?: boolean; compliance?: { violations?: string[] } }>;
  has_final_document?: boolean;
};

export default function RfpPage() {
  const [ticketId, setTicketId] = useState("");
  const [progress, setProgress] = useState<TicketProgress | null>(null);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  async function refresh(id: string) {
    const response = await fetch(incidentsUrl(`/api/rfp/${id}`));
    if (!response.ok) {
      setMessage("Unable to load ticket progress.");
      return;
    }
    setProgress(await response.json());
  }

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("rfpFile") as HTMLInputElement;
    if (!fileInput.files?.length) {
      setMessage("Choose a PDF or text RFP file.");
      return;
    }
    setUploading(true);
    setMessage("");
    const body = new FormData();
    body.append("file", fileInput.files[0]);
    const response = await fetch(incidentsUrl("/api/rfp/upload"), {
      method: "POST",
      body,
    });
    setUploading(false);
    if (!response.ok) {
      setMessage("Upload failed.");
      return;
    }
    const payload = await response.json();
    setTicketId(payload.ticket_id);
    setMessage(`Upload accepted. Ticket ${payload.ticket_id} is ${payload.status}.`);
    await refresh(payload.ticket_id);
  }

  async function resume(departmentId: string, decision: "approve" | "reject" | "request_changes") {
    if (!ticketId) return;
    const response = await fetch(incidentsUrl(`/api/rfp/${ticketId}/resume`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ department_id: departmentId, decision }),
    });
    if (!response.ok) {
      setMessage(`Resume failed for ${departmentId}.`);
      return;
    }
    setMessage(`${departmentId} decision recorded: ${decision}`);
    await refresh(ticketId);
  }

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">TrackFlow RFP Workflow</h1>
        <p className="text-sm text-gray-600">
          Upload an RFP, poll ticket progress, and approve department sections.
        </p>
      </header>

      <form onSubmit={onUpload} className="rounded border p-4">
        <label className="block text-sm font-medium">RFP document</label>
        <input type="file" name="rfpFile" accept=".pdf,.txt" className="mt-2" />
        <button
          type="submit"
          disabled={uploading}
          className="mt-3 rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Upload RFP"}
        </button>
      </form>

      {ticketId ? (
        <section className="rounded border p-4">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-medium">Ticket {ticketId}</h2>
            <button
              type="button"
              onClick={() => refresh(ticketId)}
              className="rounded border px-3 py-1 text-sm"
            >
              Refresh
            </button>
          </div>
          {progress ? (
            <div className="mt-4 space-y-3">
              <p>Status: {progress.status}</p>
              {Object.entries(progress.departments).map(([departmentId, dept]) => {
                const evaluation = progress.evaluations[departmentId];
                return (
                  <div key={departmentId} className="rounded border p-3">
                    <p className="font-medium">{departmentId}</p>
                    <p className="text-sm">Department status: {dept.status ?? "unknown"}</p>
                    <p className="text-sm">
                      Evaluation pass: {evaluation?.overall_pass ? "yes" : "no"}
                    </p>
                    {evaluation?.compliance?.violations?.length ? (
                      <p className="text-sm text-red-700">
                        Violations: {evaluation.compliance.violations.join("; ")}
                      </p>
                    ) : null}
                    <div className="mt-2 flex gap-2">
                      <button
                        type="button"
                        className="rounded border px-2 py-1 text-sm"
                        onClick={() => resume(departmentId, "approve")}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        className="rounded border px-2 py-1 text-sm"
                        onClick={() => resume(departmentId, "reject")}
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                );
              })}
              {progress.has_final_document ? (
                <a
                  className="text-blue-700 underline"
                  href={incidentsUrl(`/api/rfp/${ticketId}/document`)}
                >
                  Download final document
                </a>
              ) : null}
            </div>
          ) : null}
        </section>
      ) : null}

      {message ? <p className="text-sm text-gray-700">{message}</p> : null}
    </main>
  );
}
