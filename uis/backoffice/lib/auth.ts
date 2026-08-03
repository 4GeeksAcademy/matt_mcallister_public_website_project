const TOKEN_STORAGE_KEY = "trackflow_jwt_token";

const decodeBase64Url = (value: string) => {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");

  if (typeof window === "undefined") {
    return "";
  }

  return window.atob(padded);
};

const getTokenPayload = (token: string): { exp?: number } | null => {
  try {
    const [, payloadPart] = token.split(".");

    if (!payloadPart) {
      return null;
    }

    const decoded = decodeBase64Url(payloadPart);

    if (!decoded) {
      return null;
    }

    return JSON.parse(decoded) as { exp?: number };
  } catch {
    return null;
  }
};

export const getToken = () => {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
};

export const setToken = (token: string) => {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

export const clearToken = () => {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
};

export const isTokenValid = (token: string | null) => {
  if (!token) {
    return false;
  }

  const parts = token.split(".");
  if (parts.length !== 3) {
    return false;
  }

  const payload = getTokenPayload(token);
  if (!payload) {
    return false;
  }

  if (!payload.exp) {
    return true;
  }

  const nowSeconds = Math.floor(Date.now() / 1000);
  return payload.exp > nowSeconds;
};

export const hasValidSession = () => isTokenValid(getToken());

export const logout = () => {
  clearToken();

  if (typeof window !== "undefined") {
    window.location.assign("/login");
  }
};
