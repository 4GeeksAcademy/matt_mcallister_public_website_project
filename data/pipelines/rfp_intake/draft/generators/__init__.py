"""Per-department proposal section generators."""

from __future__ import annotations

from typing import Any

from data.pipelines.rfp_intake.draft.generators import lastmile, reverse, warehouse
from data.pipelines.rfp_intake.models import DepartmentSummary, SectionDraft

_GENERATORS = {
    "warehouse": warehouse.generate,
    "lastmile": lastmile.generate,
    "reverse": reverse.generate,
}


def generate_section(
    *,
    department_id: str,
    summary: DepartmentSummary,
    metadata: dict[str, Any] | None = None,
    previous_draft: SectionDraft | None = None,
    feedback: str = "",
) -> SectionDraft:
    generator = _GENERATORS.get(department_id)
    if generator is None:
        raise ValueError(f"No generator for department: {department_id}")
    return generator(
        summary=summary,
        metadata=metadata or {},
        previous_draft=previous_draft,
        feedback=feedback,
    )
