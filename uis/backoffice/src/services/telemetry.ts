/**
 * TrackFlow client-side telemetry service.
 * All backoffice tracking goes through track() — never direct fetch/axios for events.
 */
import type {
  TelemetryEvent,
  TelemetryEventType,
  TelemetryPropertyMap,
  Warehouse,
  ProductCategory,
} from "../../../../packages/shared/types/telemetry";

export const SCHEMA_VERSION = "1.0.0";
export type { Warehouse, ProductCategory };

const FLUSH_INTERVAL_MS = 10_000;
const MAX_QUEUE_SIZE = 20;
const MAX_RETRIES = 3;

const queue: TelemetryEvent[] = [];
let flushTimer: ReturnType<typeof setInterval> | null = null;
let sessionId = "sess_anonymous";
let userId = "anonymous";
let initialized = false;

const STREAM_TYPES: Set<TelemetryEventType> = new Set([
  "stock_threshold_triggered",
  "direct_stock_edit_rejected",
  "user_login_failed",
  "frontend_error_uncaught",
]);

function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `id_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function endpoint(): string {
  return (
    process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT ||
    "http://127.0.0.1:8005/telemetry/events"
  );
}

export function setTelemetryIdentity(nextUserId: string, nextSessionId: string) {
  userId = nextUserId;
  sessionId = nextSessionId;
}

export function getTelemetryIdentity() {
  return { userId, sessionId };
}

function ensureTimer() {
  if (typeof window === "undefined") return;
  if (flushTimer) return;
  flushTimer = setInterval(() => {
    void flush(false);
  }, FLUSH_INTERVAL_MS);
}

function onVisibilityChange() {
  if (document.visibilityState === "hidden") {
    beaconFlush();
  }
}

export function initTelemetry() {
  if (typeof window === "undefined" || initialized) return;
  initialized = true;
  ensureTimer();
  document.addEventListener("visibilitychange", onVisibilityChange);

  window.onerror = (message, source) => {
    track("frontend_error_uncaught", {
      message: String(message).slice(0, 200),
      path: window.location.pathname,
      source: String(source || "window.onerror"),
    });
  };
  window.onunhandledrejection = (event) => {
    track("frontend_error_uncaught", {
      message: String(event.reason).slice(0, 200),
      path: window.location.pathname,
      source: "unhandledrejection",
    });
  };
}

function beaconFlush() {
  if (!queue.length) return;
  const batch = queue.splice(0, queue.length);
  const payload = JSON.stringify({ events: batch });
  const url = endpoint();
  if (navigator.sendBeacon) {
    const blob = new Blob([payload], { type: "application/json" });
    navigator.sendBeacon(url, blob);
    return;
  }
  void sendWithRetry(batch, 0);
}

async function sendWithRetry(
  batch: TelemetryEvent[],
  attempt: number
): Promise<boolean> {
  try {
    const res = await fetch(endpoint(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: batch }),
    });
    if (!res.ok) throw new Error(`status ${res.status}`);
    return true;
  } catch {
    if (attempt >= MAX_RETRIES) {
      return false;
    }
    const wait = 2 ** attempt * 250;
    await new Promise((r) => setTimeout(r, wait));
    return sendWithRetry(batch, attempt + 1);
  }
}

async function flush(force: boolean) {
  if (!queue.length) return;
  if (!force && queue.length < MAX_QUEUE_SIZE) {
    // interval flush still sends whatever is pending
  }
  const batch = queue.splice(0, queue.length);
  const ok = await sendWithRetry(batch, 0);
  if (!ok) {
    // discharged after retries per plan
  }
}

/**
 * Capture an event. Envelope fields are filled automatically.
 */
export function track<T extends TelemetryEventType>(
  eventType: T,
  properties: TelemetryPropertyMap[T]
): void {
  if (typeof window === "undefined") return;
  initTelemetry();

  const event = {
    eventId: uuid(),
    timestamp: new Date().toISOString(),
    sessionId,
    userId,
    event_type: eventType,
    schemaVersion: SCHEMA_VERSION,
    requestId: uuid(),
    properties: { ...properties },
  } as TelemetryEvent;
  queue.push(event);

  if (queue.length >= MAX_QUEUE_SIZE || STREAM_TYPES.has(eventType)) {
    void flush(true);
  }
}

export async function flushNow() {
  await flush(true);
}

export async function timedFetch(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const started = performance.now();
  const method = (init?.method || "GET").toUpperCase();
  const url = typeof input === "string" ? input : input.toString();
  let status = 0;
  try {
    const res = await fetch(input, init);
    status = res.status;
    return res;
  } finally {
    track("api_latency_recorded", {
      endpoint: url.replace(/^https?:\/\/[^/]+/, ""),
      method,
      status_code: status,
      duration_ms: Math.round(performance.now() - started),
    });
  }
}
