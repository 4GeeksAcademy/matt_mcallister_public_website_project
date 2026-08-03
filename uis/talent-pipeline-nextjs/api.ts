const API_PREFIX = '/tracker/api/v1';

function trimTrailingSlash(url: string): string {
  return url.replace(/\/$/, '');
}

function getBaseUrl(): string {
  const fullApiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (fullApiUrl) {
    return trimTrailingSlash(fullApiUrl);
  }

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (apiBaseUrl) {
    return `${trimTrailingSlash(apiBaseUrl)}${API_PREFIX}`;
  }

  // Node's fetch requires an absolute URL. In the browser we can keep a relative path.
  if (typeof window === 'undefined') {
    const appUrl =
      process.env.NEXT_PUBLIC_APP_URL ??
      process.env.APP_URL ??
      'http://localhost:3000';
    return `${trimTrailingSlash(appUrl)}${API_PREFIX}`;
  }

  return API_PREFIX;
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${getBaseUrl()}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  // 204 No Content — nothing to parse
  if (res.status === 204) return undefined as T;

  const data = await res.json();

  if (!res.ok) {
    // API returns { detail: ValidationError[] } on 422
    const message =
      data?.detail?.[0]?.msg ?? data?.detail ?? `API error ${res.status}`;
    throw new Error(message);
  }

  return data as T;
}