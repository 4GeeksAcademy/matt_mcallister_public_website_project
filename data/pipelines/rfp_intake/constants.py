"""RFP workflow constants."""

from __future__ import annotations

MAX_SECTION_ITERATIONS = 3

# Part 1
STATUS_ANALYZING = "analyzing"
STATUS_INTAKE_COMPLETE = "intake_complete"
STATUS_DISCARDED = "discarded"

# Part 2
STATUS_DRAFTING = "drafting"
STATUS_UNDER_EVALUATION = "under_evaluation"
STATUS_NEEDS_HUMAN_REVIEW = "needs_human_review"

# Part 3 / terminal
STATUS_WAITING_APPROVAL = "waiting_for_approval"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

HUMAN_APPROVE = "approve"
HUMAN_REJECT = "reject"
HUMAN_REQUEST_CHANGES = "request_changes"

DEPT_APPROVED = "approved"
DEPT_PENDING = "pending"
DEPT_NEEDS_REVIEW = "needs_human_review"
DEPT_REJECTED = "rejected"
