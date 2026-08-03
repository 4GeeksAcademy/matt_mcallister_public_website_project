import { clearToken, getToken } from "@/lib/auth";

export class ApiError extends Error {
  status: number;
  fieldErrors?: Record<string, string>;

  constructor(message: string, status: number, fieldErrors?: Record<string, string>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

type ApiRequestOptions = RequestInit & {
  requireAuth?: boolean;
};

type User = {
  id: string;
  name: string;
  email: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:3001";
const LOGIN_ENDPOINT = process.env.NEXT_PUBLIC_LOGIN_ENDPOINT ?? "/auth/login";
const REGISTER_ENDPOINT = process.env.NEXT_PUBLIC_REGISTER_ENDPOINT ?? "/auth/register";
const ME_ENDPOINT = process.env.NEXT_PUBLIC_ME_ENDPOINT ?? "/users/me";
const CHANGE_PASSWORD_ENDPOINT_TEMPLATE =
  process.env.NEXT_PUBLIC_CHANGE_PASSWORD_ENDPOINT ?? "/users/{id}/change-password";

const getErrorMessage = (errorBody: unknown, fallback: string) => {
  if (typeof errorBody !== "object" || !errorBody) {
    return fallback;
  }

  const candidate = (errorBody as { message?: unknown }).message;
  if (typeof candidate === "string" && candidate.trim().length > 0) {
    return candidate;
  }

  return fallback;
};

const getValidationErrors = (errorBody: unknown): Record<string, string> | undefined => {
  if (typeof errorBody !== "object" || !errorBody) {
    return undefined;
  }

  const body = errorBody as {
    errors?: unknown;
    fieldErrors?: unknown;
  };

  if (body.fieldErrors && typeof body.fieldErrors === "object") {
    const next: Record<string, string> = {};

    Object.entries(body.fieldErrors as Record<string, unknown>).forEach(([key, value]) => {
      if (typeof value === "string") {
        next[key] = value;
      }

      if (Array.isArray(value) && typeof value[0] === "string") {
        next[key] = value[0];
      }
    });

    if (Object.keys(next).length > 0) {
      return next;
    }
  }

  if (Array.isArray(body.errors)) {
    const next: Record<string, string> = {};

    body.errors.forEach((item) => {
      if (typeof item !== "object" || !item) {
        return;
      }

      const field = (item as { field?: unknown; path?: unknown }).field;
      const path = (item as { field?: unknown; path?: unknown }).path;
      const message = (item as { message?: unknown }).message;
      const key = typeof field === "string" ? field : typeof path === "string" ? path : null;

      if (key && typeof message === "string") {
        next[key] = message;
      }
    });

    if (Object.keys(next).length > 0) {
      return next;
    }
  }

  if (body.errors && typeof body.errors === "object") {
    const next: Record<string, string> = {};

    Object.entries(body.errors as Record<string, unknown>).forEach(([key, value]) => {
      if (typeof value === "string") {
        next[key] = value;
      }

      if (Array.isArray(value) && typeof value[0] === "string") {
        next[key] = value[0];
      }
    });

    if (Object.keys(next).length > 0) {
      return next;
    }
  }

  return undefined;
};

const handleUnauthorized = () => {
  clearToken();

  if (typeof window !== "undefined") {
    window.location.assign("/login");
  }
};

const normalizeUser = (payload: unknown): User => {
  const raw =
    typeof payload === "object" && payload && "user" in payload
      ? (payload as { user?: unknown }).user
      : payload;

  if (typeof raw !== "object" || !raw) {
    throw new ApiError("Unable to parse user profile.", 500);
  }

  const candidate = raw as {
    id?: unknown;
    userId?: unknown;
    _id?: unknown;
    name?: unknown;
    email?: unknown;
  };

  const id = candidate.id ?? candidate.userId ?? candidate._id;

  if ((typeof id !== "string" && typeof id !== "number") || typeof candidate.email !== "string") {
    throw new ApiError("User profile is missing required fields.", 500);
  }

  return {
    id: String(id),
    name: typeof candidate.name === "string" ? candidate.name : "",
    email: candidate.email,
  };
};

const getJson = async (response: Response) => {
  try {
    return (await response.json()) as unknown;
  } catch {
    return null;
  }
};

export const apiRequest = async <T>(path: string, options: ApiRequestOptions = {}) => {
  const { requireAuth = true, headers, ...rest } = options;

  const requestHeaders = new Headers(headers);

  if (!requestHeaders.has("Content-Type") && rest.body) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (requireAuth) {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      throw new ApiError("You need to sign in to continue.", 401);
    }

    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
  });

  if (response.status === 401 && requireAuth) {
    handleUnauthorized();
    throw new ApiError("Your session has expired. Please sign in again.", 401);
  }

  if (!response.ok) {
    const errorBody = await getJson(response);
    const fallbackMessage = "Request failed. Please try again.";
    const message = getErrorMessage(errorBody, fallbackMessage);
    const fieldErrors = getValidationErrors(errorBody);

    throw new ApiError(message, response.status, fieldErrors);
  }

  const payload = await getJson(response);
  return payload as T;
};

type AuthResponse = {
  token: string;
};

export const authApi = {
  async login(email: string, password: string) {
    return apiRequest<AuthResponse>(LOGIN_ENDPOINT, {
      method: "POST",
      requireAuth: false,
      body: JSON.stringify({ email, password }),
    });
  },
  async register(name: string, email: string, password: string) {
    return apiRequest<AuthResponse>(REGISTER_ENDPOINT, {
      method: "POST",
      requireAuth: false,
      body: JSON.stringify({ name, email, password }),
    });
  },
};

export const userApi = {
  async getMe() {
    const data = await apiRequest<unknown>(ME_ENDPOINT, {
      method: "GET",
    });

    return normalizeUser(data);
  },
  async updateName(id: string, name: string) {
    await apiRequest(`/users/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name }),
    });
  },
  async changePassword(id: string, currentPassword: string, newPassword: string) {
    const endpoint = CHANGE_PASSWORD_ENDPOINT_TEMPLATE.replace("{id}", id);

    await apiRequest(endpoint, {
      method: "PUT",
      body: JSON.stringify({ currentPassword, newPassword }),
    });
  },
};
