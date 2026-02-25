"""Flask routes for the rollout viewer."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

import config
from export.sft_exporter import export_file

bp = Blueprint("viewer", __name__)

ROLLOUTS_DIR = config.ROLLOUTS_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_rollout_files() -> list[dict]:
    files = sorted(ROLLOUTS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    result = []
    for f in files:
        lines = sum(1 for _ in f.open(encoding="utf-8"))
        result.append({"name": f.name, "lines": lines, "size_kb": round(f.stat().st_size / 1024, 1)})
    return result


def _read_rollouts(filename: str) -> list[dict]:
    path = ROLLOUTS_DIR / filename
    if not path.exists():
        abort(404)
    rollouts = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rollouts.append(json.loads(line))
    return rollouts


def _find_rollout(rollouts: list[dict], task_id: str, sample_index: int) -> tuple[int, dict] | tuple[None, None]:
    for i, r in enumerate(rollouts):
        if r.get("task_id") == task_id and r.get("sample_index") == sample_index:
            return i, r
    return None, None


def _write_rollouts(filename: str, rollouts: list[dict]) -> None:
    """Atomically rewrite JSONL file."""
    path = ROLLOUTS_DIR / filename
    tmp_fd, tmp_path = tempfile.mkstemp(dir=ROLLOUTS_DIR, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            for r in rollouts:
                f.write(json.dumps(r) + "\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route("/")
def index():
    files = _list_rollout_files()
    return render_template("index.html", files=files)


@bp.route("/rollouts/<filename>")
def rollout_list(filename: str):
    rollouts = _read_rollouts(filename)
    return render_template("rollout_list.html", filename=filename, rollouts=rollouts)


@bp.route("/rollouts/<filename>/<task_id>")
def rollout_detail(filename: str, task_id: str):
    sample_index = int(request.args.get("sample", 0))
    rollouts = _read_rollouts(filename)
    idx, rollout = _find_rollout(rollouts, task_id, sample_index)
    if rollout is None:
        abort(404)
    return render_template(
        "rollout_detail.html",
        filename=filename,
        rollout=rollout,
        rollout_index=idx,
        total=len(rollouts),
        prev_rollout=rollouts[idx - 1] if idx > 0 else None,
        next_rollout=rollouts[idx + 1] if idx < len(rollouts) - 1 else None,
    )


@bp.route("/rollouts/<filename>/<task_id>/edit", methods=["POST"])
def edit_rollout(filename: str, task_id: str):
    sample_index = int(request.args.get("sample", 0))
    rollouts = _read_rollouts(filename)
    idx, rollout = _find_rollout(rollouts, task_id, sample_index)
    if rollout is None:
        abort(404)

    data = request.get_json(force=True)

    rollout["edited_thinking"] = data.get("edited_thinking") or None
    rollout["edited_answer"] = data.get("edited_answer") or None
    rollout["edit_note"] = data.get("edit_note") or None
    rollout["edited_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rollout["include_in_export"] = bool(data.get("include_in_export", True))

    rollouts[idx] = rollout
    _write_rollouts(filename, rollouts)

    return jsonify({"status": "ok", "edited_at": rollout["edited_at"]})


@bp.route("/rollouts/<filename>/export")
def export_rollouts(filename: str):
    """Download SFT JSONL for a rollout file."""
    path = ROLLOUTS_DIR / filename
    if not path.exists():
        abort(404)

    lines = export_file(path)
    content = "\n".join(json.dumps(r) for r in lines) + "\n"

    from flask import Response
    return Response(
        content,
        mimetype="application/x-ndjson",
        headers={"Content-Disposition": f"attachment; filename=sft_{filename}"},
    )
