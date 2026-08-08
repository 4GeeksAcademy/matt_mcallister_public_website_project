"""RFP intake: classifier, workers, and synthesizer."""

from __future__ import annotations

import re
from typing import Any

from data.pipelines.rfp_intake.context_config import (
    COUNTRY_CURRENCY,
    DEPARTMENT_BY_ID,
    DEPARTMENTS,
    NON_RFP_MARKERS,
    RFP_CLASSIFIER_MARKERS,
    SERVICE_KEYWORDS,
)
from data.pipelines.rfp_intake.models import DepartmentSummary
from data.pipelines.rfp_intake.pdf_utils import compute_readability_metrics


def classify_document(text: str) -> dict[str, Any]:
    lowered = text.casefold()
    if any(marker in lowered for marker in NON_RFP_MARKERS):
        return {"is_rfp": False, "reason": "non_rfp_document_markers"}
    score = sum(1 for marker in RFP_CLASSIFIER_MARKERS if marker in lowered)
    return {"is_rfp": score >= 2, "reason": "rfp_markers" if score >= 2 else "insufficient_rfp_markers"}


def _extract_services(text: str) -> list[str]:
    services: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            services.append(stripped[2:])
    if services:
        return services
    lowered = text.casefold()
    for keyword in SERVICE_KEYWORDS:
        if keyword in lowered:
            services.append(keyword)
    return services


def _detect_client_country(text: str) -> str:
    lowered = text.casefold()
    if any(token in lowered for token in ("spain", "zaragoza", "eur", "modaviva")):
        return "Spain"
    if any(token in lowered for token in ("united states", " los angeles", "la)", "usd", "luna cosmetics")):
        return "US"
    country_match = re.search(r"country(?:\s+of\s+origin)?:\s*(.+)", text, re.IGNORECASE)
    if country_match:
        value = country_match.group(1).strip()
        if "spain" in value.casefold():
            return "Spain"
        if "us" in value.casefold() or "united states" in value.casefold():
            return "US"
    return "US"


def extract_metadata(text: str) -> dict[str, Any]:
    client_match = re.search(r"Client:\s*(.+)", text, re.IGNORECASE)
    date_match = re.search(r"(?:Submission deadline|Deadline):\s*(.+)", text, re.IGNORECASE)
    volume_match = re.search(
        r"(\d[\d,]*)\s+orders?\s*/\s*month",
        text,
        re.IGNORECASE,
    )
    budget_match = re.search(r"(?:Budget|Reference budget):\s*(.+)", text, re.IGNORECASE)
    services_requested = _extract_services(text)
    client_country = _detect_client_country(text)
    monthly_volume = int(volume_match.group(1).replace(",", "")) if volume_match else None
    return {
        "client_name": (client_match.group(1).strip() if client_match else "Unknown Client"),
        "client_country": client_country,
        "services_requested": services_requested,
        "monthly_volume": monthly_volume,
        "deadline": (date_match.group(1).strip() if date_match else ""),
        "budget_range": (budget_match.group(1).strip() if budget_match else ""),
        "currency": COUNTRY_CURRENCY.get(client_country, "USD"),
        "departments_needed": orchestrate_departments(text, services_requested),
    }


def orchestrate_departments(text: str, services_requested: list[str] | None = None) -> list[str]:
    services_requested = services_requested or _extract_services(text)
    assigned: set[str] = set()
    for service in services_requested:
        service_lower = service.casefold()
        if "not in scope" in service_lower:
            continue
        for keyword, department_id in SERVICE_KEYWORDS.items():
            if keyword in service_lower:
                assigned.add(department_id)
    if not assigned:
        combined = text.casefold()
        for keyword, department_id in SERVICE_KEYWORDS.items():
            if keyword in combined:
                assigned.add(department_id)
    for dept in DEPARTMENTS:
        if dept.section_heading.casefold() in text.casefold():
            assigned.add(dept.department_id)
    return sorted(assigned)


def run_department_worker(department_id: str, text: str, metadata: dict[str, Any] | None = None) -> DepartmentSummary:
    dept = DEPARTMENT_BY_ID[department_id]
    section_pattern = re.compile(
        rf"{re.escape(dept.section_heading)}(.*?)(?:\n##|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    match = section_pattern.search(text)
    excerpt = match.group(1).strip() if match else ""
    aspects = [aspect for aspect in dept.required_aspects if aspect.casefold() in excerpt.casefold()]
    if not aspects:
        aspects = [aspect for aspect in dept.required_aspects if aspect.casefold() in text.casefold()]
    if not aspects:
        aspects = list(dept.required_aspects[:2])
    if metadata and metadata.get("monthly_volume") is None and department_id == "warehouse":
        aspects = list(aspects) + ["open question: monthly volume not stated in RFP"]
    return DepartmentSummary(
        department_id=department_id,
        key_aspects=aspects,
        contact_name=dept.contact_name,
        contact_email=dept.contact_email,
        raw_excerpt=excerpt[:500],
    )


def synthesize_intake(
    *,
    text: str,
    department_ids: list[str],
) -> tuple[list[DepartmentSummary], dict[str, Any]]:
    metadata = extract_metadata(text)
    if not department_ids:
        department_ids = metadata["departments_needed"]
    metadata["departments_needed"] = department_ids
    summaries = [run_department_worker(dept_id, text, metadata) for dept_id in department_ids]
    readability = compute_readability_metrics(text)
    return summaries, {"metadata": metadata, "readability_metrics": readability}
