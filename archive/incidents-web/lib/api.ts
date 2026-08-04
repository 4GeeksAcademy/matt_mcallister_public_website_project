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

const API_BASE =
  process.env.NEXT_PUBLIC_INCIDENTS_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8001";

export function getApiBase(): string {
  return API_BASE.replace(/\/$/, "");
}

export async function analyzeCsv(file: File): Promise<AnalysisResult> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${getApiBase()}/api/incidents/analyze`, {
    method: "POST",
    body,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail =
      typeof payload.detail === "string"
        ? payload.detail
        : "Unable to analyze the uploaded CSV.";
    throw new Error(detail);
  }

  return payload as AnalysisResult;
}

export async function downloadResultsCsv(): Promise<Blob> {
  const response = await fetch(`${getApiBase()}/api/incidents/results/export`, {
    method: "GET",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail =
      typeof payload.detail === "string"
        ? payload.detail
        : "No analysis results available to export.";
    throw new Error(detail);
  }

  return response.blob();
}
