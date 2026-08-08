"""TrackFlow RFP department and compliance configuration (Milestone 9)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DepartmentConfig:
    department_id: str
    title: str
    contact_name: str
    contact_email: str
    section_heading: str
    required_aspects: tuple[str, ...]


DEPARTMENTS: tuple[DepartmentConfig, ...] = (
    DepartmentConfig(
        department_id="warehouse",
        title="Warehouse Operations",
        contact_name="Ana Whitfield",
        contact_email="ana.whitfield@trackflow.com",
        section_heading="Warehouse Operations",
        required_aspects=("storage capacity", "cost per pallet/SKU", "onboarding time"),
    ),
    DepartmentConfig(
        department_id="lastmile",
        title="Last Mile and Carrier Management",
        contact_name="Carlos Vega",
        contact_email="carlos.vega@trackflow.com",
        section_heading="Last Mile and Carrier Management",
        required_aspects=("cost per shipment", "available carriers", "delivery SLA"),
    ),
    DepartmentConfig(
        department_id="reverse",
        title="Reverse Logistics",
        contact_name="Sofía Ramos",
        contact_email="sofia.ramos@trackflow.com",
        section_heading="Reverse Logistics",
        required_aspects=("returns processing cost", "returns turnaround time"),
    ),
)

DEPARTMENT_BY_ID = {dept.department_id: dept for dept in DEPARTMENTS}

SERVICE_KEYWORDS: dict[str, str] = {
    "warehousing": "warehouse",
    "warehouse": "warehouse",
    "storage": "warehouse",
    "last mile": "lastmile",
    "last-mile": "lastmile",
    "lastmile": "lastmile",
    "carrier": "lastmile",
    "returns": "reverse",
    "reverse logistics": "reverse",
    "reverse": "reverse",
}

COUNTRY_CURRENCY: dict[str, str] = {
    "US": "USD",
    "United States": "USD",
    "Spain": "EUR",
    "ES": "EUR",
}

COMPLIANCE_RULES: dict[str, str] = {
    "CURRENCY_US_USD": "Pricing for US operations must be quoted in USD.",
    "CURRENCY_SPAIN_EUR": "Pricing for Spain operations must be quoted in EUR.",
    "ONTIME_SLA_REQUIRED": (
        "Every proposal must state the on-time delivery SLA (%) TrackFlow is committing to."
    ),
    "RETURNS_UNDER_48H_FORBIDDEN": (
        "No proposal may promise returns processing in under 48 hours."
    ),
    "VOLUME_DISCOUNT_TIER_REQUIRED": (
        "Every proposal must include a volume-based discount tier table."
    ),
    "NO_CARRIER_NEGOTIATED_RATES": (
        "No proposal may disclose negotiated rates with specific carriers."
    ),
}

ARBITRATION_RULES: dict[str, dict[str, str]] = {
    "volume-vs-capacity": {
        "trigger_fields": "monthly_volume,warehouse_capacity_units",
        "arbiter": "Miguel Torres",
        "resolution": "cap_volume_to_warehouse_capacity",
    },
    "returns-sla-breach": {
        "trigger_fields": "returns_turnaround_hours",
        "arbiter": "Sofía Ramos / Miguel Torres",
        "resolution": "request_changes_all_under_48h",
    },
    "currency-mismatch": {
        "trigger_fields": "quoted_currency,client_country",
        "arbiter": "Miguel Torres",
        "resolution": "rewrite_to_country_currency",
    },
}

RFP_CLASSIFIER_MARKERS = (
    "request for proposal",
    "pricing proposal",
    "rfp",
    "trackflow",
    "warehousing",
    "warehouse operations",
    "delivery sla",
    "returns",
    "logistics proposal",
)

NON_RFP_MARKERS = (
    "incident_id",
    "customer_email",
    "satisfaction_score",
    "carrier rate pitch",
    "negotiated carrier rate",
    "partnership opportunity for carriers",
    "rate sheet for your review",
)
