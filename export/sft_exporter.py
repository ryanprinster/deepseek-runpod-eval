"""Convert edited rollouts to SFT JSONL format.

Usage (CLI):
    python -m export.sft_exporter data/rollouts/<file>.jsonl output.jsonl

Usage (library):
    from export.sft_exporter import export_file
    records = export_file(Path("data/rollouts/foo.jsonl"))
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SFT_USER_TEMPLATE = "Solve the following Python programming problem.\n\n{prompt}"
SFT_ASSISTANT_TEMPLATE = "<think>\n{thinking}\n</think>\n\n{code}"


def _to_sft(rollout: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a single rollout to SFT format, or None if filtered out."""
    if not rollout.get("pass_original_test", False):
        return None
    if not rollout.get("include_in_export", True):
        return None

    thinking = rollout.get("edited_thinking") or rollout.get("original_thinking") or ""
    code = rollout.get("edited_answer") or rollout.get("original_answer") or ""
    prompt = rollout.get("prompt") or ""
    was_edited = bool(rollout.get("edited_thinking") or rollout.get("edited_answer"))

    user_content = SFT_USER_TEMPLATE.format(prompt=prompt)
    assistant_content = SFT_ASSISTANT_TEMPLATE.format(thinking=thinking, code=code)

    return {
        "messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ],
        "metadata": {
            "task_id": rollout.get("task_id"),
            "split": rollout.get("split"),
            "sample_index": rollout.get("sample_index"),
            "model": rollout.get("model"),
            "was_edited": was_edited,
            "edited_at": rollout.get("edited_at"),
            "pass_original_test": rollout.get("pass_original_test"),
            "pass_impossible_test": rollout.get("pass_impossible_test"),
        },
    }


def export_file(input_path: Path) -> list[dict[str, Any]]:
    """Read a rollout JSONL and return SFT records (filtered)."""
    records = []
    with input_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rollout = json.loads(line)
            sft = _to_sft(rollout)
            if sft is not None:
                records.append(sft)
    return records


def export_to_file(input_path: Path, output_path: Path) -> int:
    """Export and write to output_path. Returns number of records written."""
    records = export_file(input_path)
    with output_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export rollouts to SFT JSONL")
    parser.add_argument("input", type=Path, help="Input rollout JSONL file")
    parser.add_argument("output", type=Path, help="Output SFT JSONL file")
    args = parser.parse_args()

    n = export_to_file(args.input, args.output)
    print(f"Exported {n} records → {args.output}")


if __name__ == "__main__":
    main()
