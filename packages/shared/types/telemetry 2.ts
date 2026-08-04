/**
 * TrackFlow telemetry envelope and event property types.
 * Mirrors data/pipelines/telemetry-stream/event-schemas.json (schemaVersion 1.0.0).
 * See docs/telemetry/telemetry-plan.md for rationale and delivery strategy.
 */

export const TELEMETRY_SCHEMA_VERSION = "1.0.0" as const;

export type WarehouseLocation = "los_angeles" | "zaragoza";

export type TelemetryEventType =
  | "session_started"
  | "credential_failed"
  | "session_expired"
  | "product_created"
  | "product_create_rejected"
  | "inbound_order_created"
  | "outbound_order_created"
  | "outbound_order_rejected"
  | "stock_threshold_triggered"
  | "page_viewed"
  | "form_abandoned";

export interface TelemetryEnvelope<T extends TelemetryEventType, P> {
  eventId: string;
  timestamp: string;
  sessionId: string;
  userId: string;
  event_type: T;
  schemaVersion: typeof TELEMETRY_SCHEMA_VERSION;
  requestId: string;
  properties: P;
}

export interface SessionStartedProperties {
  auth_method: "password";
  is_admin?: boolean;
}

export interface CredentialFailedProperties {
  email_hash: string;
  failure_reason: "invalid_credentials" | "account_inactive";
}

export interface SessionExpiredProperties {
  last_page: string;
  session_duration_seconds: number;
}

export interface ProductCreatedProperties {
  product_id: number;
  sku: string;
  warehouse_location: WarehouseLocation;
  client_brand: string;
  low_stock_threshold?: number;
}

export interface ProductCreateRejectedProperties {
  sku: string;
  rejection_reason: "duplicate_sku";
  existing_product_id?: number;
}

export interface InboundOrderCreatedProperties {
  order_id: number;
  product_id: number;
  sku: string;
  quantity: number;
  warehouse_location: WarehouseLocation;
  client_brand: string;
}

export interface OutboundOrderCreatedProperties {
  order_id: number;
  product_id: number;
  sku: string;
  quantity: number;
  warehouse_location: WarehouseLocation;
  resulting_stock: number;
}

export interface OutboundOrderRejectedProperties {
  product_id: number;
  sku: string;
  requested_quantity: number;
  available_stock: number;
  rejection_reason: "insufficient_stock";
}

export interface StockThresholdTriggeredProperties {
  product_id: number;
  sku: string;
  current_stock: number;
  low_stock_threshold: number;
  warehouse_location: WarehouseLocation;
  client_brand: string;
}

export interface PageViewedProperties {
  page_path: string;
  referrer_path?: string;
}

export interface FormAbandonedProperties {
  form_type: "inbound" | "outbound" | "product";
  last_field?: string;
  elapsed_seconds: number;
}

export type SessionStartedEvent = TelemetryEnvelope<
  "session_started",
  SessionStartedProperties
>;
export type CredentialFailedEvent = TelemetryEnvelope<
  "credential_failed",
  CredentialFailedProperties
>;
export type SessionExpiredEvent = TelemetryEnvelope<
  "session_expired",
  SessionExpiredProperties
>;
export type ProductCreatedEvent = TelemetryEnvelope<
  "product_created",
  ProductCreatedProperties
>;
export type ProductCreateRejectedEvent = TelemetryEnvelope<
  "product_create_rejected",
  ProductCreateRejectedProperties
>;
export type InboundOrderCreatedEvent = TelemetryEnvelope<
  "inbound_order_created",
  InboundOrderCreatedProperties
>;
export type OutboundOrderCreatedEvent = TelemetryEnvelope<
  "outbound_order_created",
  OutboundOrderCreatedProperties
>;
export type OutboundOrderRejectedEvent = TelemetryEnvelope<
  "outbound_order_rejected",
  OutboundOrderRejectedProperties
>;
export type StockThresholdTriggeredEvent = TelemetryEnvelope<
  "stock_threshold_triggered",
  StockThresholdTriggeredProperties
>;
export type PageViewedEvent = TelemetryEnvelope<
  "page_viewed",
  PageViewedProperties
>;
export type FormAbandonedEvent = TelemetryEnvelope<
  "form_abandoned",
  FormAbandonedProperties
>;

export type TelemetryEvent =
  | SessionStartedEvent
  | CredentialFailedEvent
  | SessionExpiredEvent
  | ProductCreatedEvent
  | ProductCreateRejectedEvent
  | InboundOrderCreatedEvent
  | OutboundOrderCreatedEvent
  | OutboundOrderRejectedEvent
  | StockThresholdTriggeredEvent
  | PageViewedEvent
  | FormAbandonedEvent;
