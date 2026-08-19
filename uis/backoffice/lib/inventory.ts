import { clearToken, getToken } from "@/lib/auth";

export class InventoryApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "InventoryApiError";
    this.status = status;
  }
}

export type WarehouseLocation = "los_angeles" | "zaragoza";

export type Product = {
  id: number;
  name: string;
  sku: string;
  warehouse_location: WarehouseLocation | string;
  client_brand: string;
  low_stock_threshold: number;
  current_stock: number;
};

export type Order = {
  id: number;
  order_type: "inbound" | "outbound";
  product_id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  created_at: string;
  user_uuid: string;
};

export type InboundOrderCreate = {
  product_id: number;
  quantity: number;
};

export type OutboundOrderCreate = {
  product_id: number;
  quantity: number;
};

type InventoryRequestOptions = RequestInit & {
  requireAuth?: boolean;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:3001";

const parseFastApiDetail = (errorBody: unknown, fallback: string) => {
  if (typeof errorBody !== "object" || !errorBody) {
    return fallback;
  }

  const detail = (errorBody as { detail?: unknown }).detail;

  if (typeof detail === "string" && detail.trim().length > 0) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (typeof item === "object" && item && "msg" in item) {
          const msg = (item as { msg?: unknown }).msg;
          return typeof msg === "string" ? msg : null;
        }

        return null;
      })
      .filter((part): part is string => Boolean(part));

    if (parts.length > 0) {
      return parts.join(" ");
    }
  }

  const message = (errorBody as { message?: unknown }).message;
  if (typeof message === "string" && message.trim().length > 0) {
    return message;
  }

  return fallback;
};

const handleUnauthorized = () => {
  clearToken();

  if (typeof window !== "undefined") {
    window.location.assign("/login");
  }
};

const getJson = async (response: Response) => {
  try {
    return (await response.json()) as unknown;
  } catch {
    return null;
  }
};

const inventoryRequest = async <T>(path: string, options: InventoryRequestOptions = {}) => {
  const { requireAuth = false, headers, ...rest } = options;
  const requestHeaders = new Headers(headers);

  if (!requestHeaders.has("Content-Type") && rest.body) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (requireAuth) {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      throw new InventoryApiError("You need to sign in to continue.", 401);
    }

    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    cache: "no-store",
  });

  if (response.status === 401 && requireAuth) {
    handleUnauthorized();
    throw new InventoryApiError("Your session has expired. Please sign in again.", 401);
  }

  if (!response.ok) {
    const errorBody = await getJson(response);
    throw new InventoryApiError(
      parseFastApiDetail(errorBody, "Inventory request failed. Please try again."),
      response.status
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await getJson(response)) as T;
};

export const inventoryApi = {
  listProducts() {
    return inventoryRequest<Product[]>("/inventory/products", {
      method: "GET",
      requireAuth: false,
    });
  },
  getProduct(productId: number) {
    return inventoryRequest<Product>(`/inventory/products/${productId}`, {
      method: "GET",
      requireAuth: false,
    });
  },
  createInboundOrder(payload: InboundOrderCreate) {
    return inventoryRequest<{ id: number; product_id: number; quantity: number }>(
      "/inventory/orders/inbound",
      {
        method: "POST",
        requireAuth: true,
        body: JSON.stringify(payload),
      }
    );
  },
  createOutboundOrder(payload: OutboundOrderCreate) {
    return inventoryRequest<{ id: number; product_id: number; quantity: number }>(
      "/inventory/orders/outbound",
      {
        method: "POST",
        requireAuth: true,
        body: JSON.stringify(payload),
      }
    );
  },
  listOrders() {
    return inventoryRequest<Order[]>("/inventory/orders", {
      method: "GET",
      requireAuth: false,
    });
  },
};

export const WAREHOUSE_LABELS: Record<string, string> = {
  los_angeles: "Los Angeles",
  zaragoza: "Zaragoza",
};

export const warehouseLabel = (location: string) => WAREHOUSE_LABELS[location] ?? location;
