const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4000";

export const apiUrls = {
  leads: `${API_BASE}/api/leads`,
  executiveSnapshot: `${API_BASE}/api/executive-snapshot`,
};

export type ApiErrorResponse = {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
  };
};

export async function parseApiError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorResponse;
    return (
      body.error?.message ??
      "Something went wrong. Please try again or contact comercial@trackflow.com for help."
    );
  } catch {
    return "Something went wrong. Please try again or contact comercial@trackflow.com for help.";
  }
}
