"""Write the hub note + machine-readable trace into the Obsidian vault."""

from __future__ import annotations

import re
from pathlib import Path

from r2a.domain.job import JobResult
from r2a.pipeline.stage import StageContext
from r2a.pipeline.tracer import Tracer

from .hub_note import render_hub_note


def _slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)[:60] or "artifact"


def write_outputs(ctx: StageContext, tracer: Tracer, out_dir: Path) -> JobResult:
    """Write the hub note and trace.json; return paths in a JobResult."""
    out_dir.mkdir(parents=True, exist_ok=True)
    draft = ctx.draft
    assert draft is not None, "nothing to write"

    base = _slug(draft.title)
    hub_path = out_dir / f"{base}.md"
    trace_path = out_dir / "trace.json"

    hub_path.write_text(render_hub_note(ctx, tracer), encoding="utf-8")
    trace_path.write_text(tracer.to_json(), encoding="utf-8")

    return JobResult(
        hub_note_path=str(hub_path),
        trace_path=str(trace_path),
        artifact_paths=[str(hub_path)],
        shipped_with_caveat=ctx.ship_with_caveat,
    )
