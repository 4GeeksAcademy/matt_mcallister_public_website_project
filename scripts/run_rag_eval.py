#!/usr/bin/env python3
"""Run TrackFlow RAG Recall@3 evaluation against data/eval/test-queries.json.

Exits non-zero when Recall@3 is below the CONTEXT-company.md threshold (0.80).

Modes:
  --local-index  Index KB docs into in-memory Qdrant with a deterministic
                 embedder and evaluate retrieval (CI path).
  --mock         Skip indexing; return expected sources via a stub retriever.
  (default)      Use the live OpenAI + Qdrant stack from environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.pipelines.rag import (  # noqa: E402
    EVAL_QUERIES_PATH,
    build_local_index_retrieve_fn,
    evaluate_recall_at_3,
)

THRESHOLD = 0.8


def build_mock_retrieve():
    cases = json.loads(EVAL_QUERIES_PATH.read_text(encoding="utf-8"))
    expected = {
        case["question"]: case["expected_source_document"] for case in cases
    }

    def retrieve(question: str, **kwargs):
        return [
            {"source_document": "noise"},
            {"source_document": expected[question]},
            {"source_document": "other"},
        ]

    return retrieve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate TrackFlow RAG Recall@3")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--local-index",
        action="store_true",
        help="Index KB docs into in-memory Qdrant with a deterministic embedder",
    )
    mode.add_argument(
        "--mock",
        action="store_true",
        help="Use a deterministic mock retriever (no indexing)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=THRESHOLD,
        help="Minimum acceptable Recall@3 (default: 0.8)",
    )
    args = parser.parse_args(argv)

    if args.mock:
        retrieve_fn = build_mock_retrieve()
        min_score = None
    elif args.local_index:
        retrieve_fn = build_local_index_retrieve_fn()
        min_score = 0.0
    else:
        retrieve_fn = None
        min_score = None

    report = evaluate_recall_at_3(retrieve_fn=retrieve_fn, min_score=min_score)
    print(json.dumps(report, indent=2))
    recall = float(report["recall_at_3"])
    if recall < args.threshold:
        print(
            f"FAIL: Recall@3={recall:.2%} is below threshold {args.threshold:.0%}",
            file=sys.stderr,
        )
        return 1
    print(f"PASS: Recall@3={recall:.2%} meets threshold {args.threshold:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
