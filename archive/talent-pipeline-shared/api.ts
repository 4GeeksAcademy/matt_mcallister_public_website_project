const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL
  ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/tracker/api/v1`
  : '/tracker/api/v1';

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
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
