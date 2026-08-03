const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4000";

export const apiUrls = {
  executiveSnapshot: `${API_BASE}/api/executive-snapshot`,
};

export type ApiErrorResponse = {
  error: {
    code: string;
    message: string;
  };
};

export async function parseApiError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorResponse;
    return (
      body.error?.message ??
      "We could not load the dashboard data. Please refresh the page or try again later."
    );
  } catch {
    return "We could not load the dashboard data. Please refresh the page or try again later.";
  }
}
