function trimTrailingSlash(url: string): string {
  return url.replace(/\/$/, '');
}

function getBaseUrl(): string {
  return trimTrailingSlash(
    process.env.NEXT_PUBLIC_TALENT_API_URL ??
      'http://localhost:8004/tracker/api/v1'
  );
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