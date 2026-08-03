export type AnalysisResult = {
  source_file: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  invalid_breakdown: Record<string, number>;
  category_counts: Record<string, number>;
  status_counts: Record<string, number>;
  country_counts: Record<string, number>;
  satisfaction_counts: Record<string, number>;
  satisfaction_average: number | null;
  scored_incidents: number;
};

const API_BASE = (
  process.env.NEXT_PUBLIC_INCIDENTS_API_URL || "http://127.0.0.1:8001"
).replace(/\/$/, "");

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const payload = await response.json().catch(() => ({}));
  return typeof payload.detail === "string" ? payload.detail : fallback;
}

export async function analyzeCsv(file: File): Promise<AnalysisResult> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${API_BASE}/api/incidents/analyze`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Unable to analyze the uploaded CSV."));
  }
  return response.json() as Promise<AnalysisResult>;
}

export async function downloadResultsCsv(): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/incidents/results/export`);
  if (!response.ok) {
    throw new Error(await errorMessage(response, "No analysis results available to export."));
  }
  return response.blob();
}
