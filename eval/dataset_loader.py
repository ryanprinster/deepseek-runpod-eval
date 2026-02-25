"""Load and parse fjzzq2002/impossible_livecodebench dataset."""
from __future__ import annotations

from typing import Any

from datasets import load_dataset


DATASET_NAME = "fjzzq2002/impossible_livecodebench"

# Map CLI split names to HuggingFace dataset splits
SPLIT_MAP = {
    "original": "original",
    "conflicting": "conflicting",
    "one_off": "oneoff",
}


def load_problems(split: str, limit: int | None = None) -> list[dict[str, Any]]:
    """Return a list of problem dicts for the given split.

    Each dict has at least:
      - task_id: str
      - entry_point: str
      - prompt: str                 (function signature + docstring)
      - original_tests: str         (test harness that should pass)
      - impossible_tests: str       (test harness that should fail)
    """
    if split not in SPLIT_MAP:
        raise ValueError(f"Unknown split '{split}'. Choose from: {list(SPLIT_MAP)}")

    ds = load_dataset(DATASET_NAME, split=SPLIT_MAP[split])

    problems = []
    for i, row in enumerate(ds):
        if limit is not None and i >= limit:
            break
        problems.append(_normalize(row))

    return problems


def _normalize(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw dataset row into a consistent schema."""
    # The dataset uses various field names — handle gracefully
    task_id = row.get("task_id") or row.get("id") or f"task_{hash(str(row))}"
    entry_point = row.get("entry_point") or row.get("function_name") or ""
    prompt = row.get("prompt") or row.get("question") or ""
    original_tests = row.get("original_tests") or row.get("test") or ""
    impossible_tests = row.get("impossible_tests") or row.get("impossible_test") or ""

    return {
        "task_id": str(task_id),
        "entry_point": str(entry_point),
        "prompt": str(prompt),
        "original_tests": str(original_tests),
        "impossible_tests": str(impossible_tests),
    }
