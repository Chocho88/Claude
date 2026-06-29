"""Write the hub note + machine-readable trace into the Obsidian vault."""

from __future__ import annotations

import re
from pathlib import Path

from r2a.domain.artifact import ArtifactType
from r2a.domain.job import JobResult
from r2a.pipeline.stage import StageContext
from r2a.pipeline.tracer import Tracer

from .deck import render_deck
from .html_prototype import render_html
from .hub_note import render_hub_note


def _slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)[:60] or "artifact"


def write_outputs(ctx: StageContext, tracer: Tracer, out_dir: Path) -> JobResult:
    """Write the hub note, requested rich artifacts, and trace.json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    draft = ctx.draft
    assert draft is not None, "nothing to write"

    base = _slug(draft.title)
    requested = set(ctx.answers.constraints.artifacts)
    artifact_paths: list[str] = []
    # Filenames passed to the hub note so it can link/embed them.
    links: dict[str, str] = {}

    # Rich artifacts first, so the hub note can reference them.
    if ArtifactType.DECK in requested:
        deck_path = out_dir / f"{base}-deck.md"
        deck_path.write_text(render_deck(ctx), encoding="utf-8")
        artifact_paths.append(str(deck_path))
        links["deck"] = deck_path.name

    if ArtifactType.HTML in requested:
        html_path = out_dir / f"{base}-prototype.html"
        html_path.write_text(render_html(ctx), encoding="utf-8")
        artifact_paths.append(str(html_path))
        links["html"] = html_path.name

    hub_path = out_dir / f"{base}.md"
    hub_path.write_text(render_hub_note(ctx, tracer, links=links), encoding="utf-8")
    artifact_paths.insert(0, str(hub_path))

    trace_path = out_dir / "trace.json"
    trace_path.write_text(tracer.to_json(), encoding="utf-8")

    return JobResult(
        hub_note_path=str(hub_path),
        trace_path=str(trace_path),
        artifact_paths=artifact_paths,
        shipped_with_caveat=ctx.ship_with_caveat,
    )
