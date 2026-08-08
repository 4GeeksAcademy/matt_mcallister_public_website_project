"""Part 2 evaluators and generator dispatch."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from data.pipelines.rfp_intake.context_config import COMPLIANCE_RULES, COUNTRY_CURRENCY
from data.pipelines.rfp_intake.draft.generators import generate_section
from data.pipelines.rfp_intake.models import (
    ComplianceResult,
    DepartmentSummary,
    EvaluationResult,
    ReadabilityResult,
    RelevanceResult,
    SectionDraft,
)

REQUIRED_PATTERNS = {
    "VOLUME_DISCOUNT_TIER_REQUIRED": re.compile(r"(?i)volume-based discount tier table"),
    "ONTIME_SLA_REQUIRED": re.compile(r"(?i)on-time delivery sla commitment:\s*\d+\s*%"),
}

FORBIDDEN_PATTERNS = {
    "RETURNS_UNDER_48H_FORBIDDEN": re.compile(
        r"(?i)(returns?\s+(processing|turnaround).{0,60}under\s+48\s*hours?|"
        r"under\s+48\s*hours?.{0,20}returns?)"
    ),
    "NO_CARRIER_NEGOTIATED_RATES": re.compile(
        r"(?i)(negotiated\s+(carrier\s+)?rate|carrier\s+negotiated\s+rate|ups\s+negotiated\s+rate)"
    ),
}


def evaluate_readability(content: str) -> ReadabilityResult:
    words = content.split()
    score = min(100.0, max(20.0, 100 - len(words) * 0.05))
    passed = len(words) >= 40
    return ReadabilityResult(pass_=passed, score=round(score, 2), details=f"word_count={len(words)}")


def evaluate_relevance(content: str, summary: DepartmentSummary) -> RelevanceResult:
    missing = [
        aspect for aspect in summary.key_aspects if aspect.casefold() not in content.casefold()
    ]
    return RelevanceResult(pass_=not missing, missing_aspects=missing)


def evaluate_compliance(content: str, *, client_country: str = "", currency: str = "") -> ComplianceResult:
    violations: list[str] = []
    rule_ids: list[str] = []

    for rule_id, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(content):
            rule_ids.append(rule_id)
            violations.append(COMPLIANCE_RULES[rule_id])

    for rule_id, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(content):
            rule_ids.append(rule_id)
            violations.append(COMPLIANCE_RULES[rule_id])

    expected_currency = COUNTRY_CURRENCY.get(client_country, currency or "USD")
    if client_country == "US" and re.search(r"(?i)\bEUR\b|\beuros?\b", content):
        rule_ids.append("CURRENCY_US_USD")
        violations.append(COMPLIANCE_RULES["CURRENCY_US_USD"])
    if client_country == "Spain" and re.search(r"(?i)\bUSD\b|\bdollars?\b", content):
        rule_ids.append("CURRENCY_SPAIN_EUR")
        violations.append(COMPLIANCE_RULES["CURRENCY_SPAIN_EUR"])
    if currency and expected_currency and currency != expected_currency:
        rule_ids.append("currency-mismatch")
        violations.append(f"Expected currency {expected_currency} for {client_country}.")

    return ComplianceResult(pass_=not violations, rule_ids=rule_ids, violations=violations)


def evaluate_section(
    *,
    department_id: str,
    draft: SectionDraft,
    summary: DepartmentSummary,
    metadata: dict[str, Any] | None = None,
) -> EvaluationResult:
    metadata = metadata or {}
    readability = evaluate_readability(draft.content)
    relevance = evaluate_relevance(draft.content, summary)
    compliance = evaluate_compliance(
        draft.content,
        client_country=metadata.get("client_country", ""),
        currency=metadata.get("currency", draft.structured_claims.get("quoted_currency", "")),
    )
    overall_pass = readability.pass_ and relevance.pass_ and compliance.pass_
    feedback_parts = []
    if not readability.pass_:
        feedback_parts.append("Expand the section with more concrete operational detail.")
    if relevance.missing_aspects:
        feedback_parts.append(
            "Cover missing aspects: " + ", ".join(relevance.missing_aspects) + "."
        )
    if not compliance.pass_:
        feedback_parts.append(
            "Remove or revise forbidden claims: " + "; ".join(compliance.violations) + "."
        )
    return EvaluationResult(
        section_id=f"{department_id}_v{draft.version}",
        department_id=department_id,
        readability=readability,
        relevance=relevance,
        compliance=compliance,
        overall_pass=overall_pass,
        feedback_for_generator=" ".join(feedback_parts),
    )


def evaluate_sections_parallel(
    items: list[tuple[SectionDraft, DepartmentSummary, dict[str, Any]]],
) -> list[EvaluationResult]:
    with ThreadPoolExecutor(max_workers=max(1, len(items))) as pool:
        futures = [
            pool.submit(
                evaluate_section,
                department_id=draft.department_id,
                draft=draft,
                summary=summary,
                metadata=metadata,
            )
            for draft, summary, metadata in items
        ]
        return [future.result() for future in futures]


__all__ = ["evaluate_compliance", "evaluate_section", "evaluate_sections_parallel", "generate_section"]
