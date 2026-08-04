"""Strict Pydantic models for the TrackFlow telemetry contract."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


SCHEMA_VERSION = "1.0.0"

Warehouse = Literal["los_angeles", "zaragoza"]
ProductCategory = Literal["fashion", "electronics", "cosmetics"]
EventType = Literal[
    "inbound_order_created",
    "outbound_order_created",
    "outbound_order_rejected",
    "stock_threshold_triggered",
    "direct_stock_edit_rejected",
    "inventory_discrepancy_detected",
    "inbound_order_validation_failed",
    "user_login_succeeded",
    "user_login_failed",
    "session_expired",
    "page_viewed",
    "page_load_recorded",
    "api_latency_recorded",
    "frontend_error_uncaught",
    "picking_duration_recorded",
    "flow_abandoned",
]


class StrictProperties(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class InventoryProperties(StrictProperties):
    warehouse: Warehouse
    client_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    product_category: ProductCategory
    quantity: int


class InboundOrderCreatedProperties(InventoryProperties):
    order_id: str = Field(min_length=1)


class OutboundOrderCreatedProperties(InventoryProperties):
    order_id: str = Field(min_length=1)


class OutboundOrderRejectedProperties(InventoryProperties):
    failure_reason: str = Field(min_length=1)


class StockThresholdTriggeredProperties(InventoryProperties):
    threshold: int = Field(ge=0)
    current_stock: int = Field(ge=0)


class DirectStockEditRejectedProperties(InventoryProperties):
    attempted_delta: int
    reason: str = Field(min_length=1)


class InventoryDiscrepancyDetectedProperties(InventoryProperties):
    system_quantity: int = Field(ge=0)
    counted_quantity: int = Field(ge=0)
    delta: int


class InboundOrderValidationFailedProperties(InventoryProperties):
    failure_reason: str = Field(min_length=1)


class UserLoginSucceededProperties(StrictProperties):
    method: Literal["password"]


class UserLoginFailedProperties(StrictProperties):
    failure_code: str = Field(min_length=1)


class SessionExpiredProperties(StrictProperties):
    last_page: str = Field(min_length=1)
    session_duration_seconds: int = Field(ge=0)


class PageViewedProperties(StrictProperties):
    path: str = Field(min_length=1)
    title: str = Field(min_length=1)


class PageLoadRecordedProperties(StrictProperties):
    path: str = Field(min_length=1)
    duration_ms: int = Field(ge=0)


class ApiLatencyRecordedProperties(StrictProperties):
    endpoint: str = Field(min_length=1)
    method: str = Field(min_length=1)
    status_code: int = Field(ge=0, le=599)
    duration_ms: int = Field(ge=0)


class FrontendErrorUncaughtProperties(StrictProperties):
    message: str = Field(min_length=1, max_length=200)
    path: str = Field(min_length=1)
    source: str = Field(min_length=1)


class PickingDurationRecordedProperties(InventoryProperties):
    order_id: str = Field(min_length=1)
    duration_ms: int = Field(ge=0)


class FlowAbandonedProperties(StrictProperties):
    flow_type: Literal["inbound", "outbound", "product"]
    elapsed_seconds: int = Field(ge=0)
    last_field: Optional[str] = None


PROPERTY_MODELS: dict[str, type[StrictProperties]] = {
    "inbound_order_created": InboundOrderCreatedProperties,
    "outbound_order_created": OutboundOrderCreatedProperties,
    "outbound_order_rejected": OutboundOrderRejectedProperties,
    "stock_threshold_triggered": StockThresholdTriggeredProperties,
    "direct_stock_edit_rejected": DirectStockEditRejectedProperties,
    "inventory_discrepancy_detected": InventoryDiscrepancyDetectedProperties,
    "inbound_order_validation_failed": InboundOrderValidationFailedProperties,
    "user_login_succeeded": UserLoginSucceededProperties,
    "user_login_failed": UserLoginFailedProperties,
    "session_expired": SessionExpiredProperties,
    "page_viewed": PageViewedProperties,
    "page_load_recorded": PageLoadRecordedProperties,
    "api_latency_recorded": ApiLatencyRecordedProperties,
    "frontend_error_uncaught": FrontendErrorUncaughtProperties,
    "picking_duration_recorded": PickingDurationRecordedProperties,
    "flow_abandoned": FlowAbandonedProperties,
}


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    eventId: str = Field(..., min_length=1)
    timestamp: str = Field(..., min_length=1)
    sessionId: str = Field(..., min_length=1)
    userId: str = Field(..., min_length=1)
    event_type: EventType
    schemaVersion: Literal["1.0.0"]
    requestId: str = Field(..., min_length=1)
    properties: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event_properties(self) -> TelemetryEvent:
        property_model = PROPERTY_MODELS[self.event_type]
        validated = property_model.model_validate(self.properties)
        self.properties = validated.model_dump(exclude_none=True)
        return self


class TelemetryBatch(BaseModel):
    """Loose batch wrapper — events validated individually in the handler."""

    model_config = ConfigDict(extra="forbid")
    events: list[Any] = Field(default_factory=list)
