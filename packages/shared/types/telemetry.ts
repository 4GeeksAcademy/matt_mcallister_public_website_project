/** TrackFlow telemetry contract (schemaVersion 1.0.0). */

export const TELEMETRY_SCHEMA_VERSION = "1.0.0" as const;

export type Warehouse = "los_angeles" | "zaragoza";
export type ProductCategory = "fashion" | "electronics" | "cosmetics";

export interface InventoryProperties {
  warehouse: Warehouse;
  client_id: string;
  product_id: string;
  product_category: ProductCategory;
  quantity: number;
}

export interface TelemetryPropertyMap {
  inbound_order_created: InventoryProperties & { order_id: string };
  outbound_order_created: InventoryProperties & { order_id: string };
  outbound_order_rejected: InventoryProperties & { failure_reason: string };
  stock_threshold_triggered: InventoryProperties & {
    threshold: number;
    current_stock: number;
  };
  direct_stock_edit_rejected: InventoryProperties & {
    attempted_delta: number;
    reason: string;
  };
  inventory_discrepancy_detected: InventoryProperties & {
    system_quantity: number;
    counted_quantity: number;
    delta: number;
  };
  inbound_order_validation_failed: InventoryProperties & {
    failure_reason: string;
  };
  user_login_succeeded: { method: "password" };
  user_login_failed: { failure_code: string };
  session_expired: {
    last_page: string;
    session_duration_seconds: number;
  };
  page_viewed: { path: string; title: string };
  page_load_recorded: { path: string; duration_ms: number };
  api_latency_recorded: {
    endpoint: string;
    method: string;
    status_code: number;
    duration_ms: number;
  };
  frontend_error_uncaught: {
    message: string;
    path: string;
    source: string;
  };
  picking_duration_recorded: InventoryProperties & {
    order_id: string;
    duration_ms: number;
  };
  flow_abandoned: {
    flow_type: "inbound" | "outbound" | "product";
    elapsed_seconds: number;
    last_field?: string;
  };
}

export type TelemetryEventType = keyof TelemetryPropertyMap;

export interface TelemetryEnvelope<T extends TelemetryEventType> {
  eventId: string;
  timestamp: string;
  sessionId: string;
  userId: string;
  event_type: T;
  schemaVersion: typeof TELEMETRY_SCHEMA_VERSION;
  requestId: string;
  properties: TelemetryPropertyMap[T];
}

export type TelemetryEvent = {
  [T in TelemetryEventType]: TelemetryEnvelope<T>;
}[TelemetryEventType];
