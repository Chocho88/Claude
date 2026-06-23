"""Collects TraceRecords and renders intent-failure localization.

Two renderings, as required:
  * `to_json()` — the machine-readable full record list.
  * `intent_timeline_callout()` — a collapsed Obsidian callout, one line per
    stage/attempt, marking the stage where intent diverged (the stage Reflection
    routed back to).
"""

from __future__ import annotations

import json

from r2a.domain.trace import RoutingTarget, StageName, TraceRecord

# Reflection's routing target -> the stage it blames.
_BLAME_STAGE = {
    RoutingTarget.PLANNING: StageName.PLANNING,
    RoutingTarget.RETRIEVAL: StageName.RETRIEVAL,
    RoutingTarget.SYNTHESIS: StageName.SYNTHESIS,
}


class Tracer:
    def __init__(self) -> None:
        self.records: list[TraceRecord] = []

    def add(self, record: TraceRecord) -> None:
        self.records.append(record)

    # ---- machine-readable ------------------------------------------------
    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(
            [r.model_dump(mode="json") for r in self.records], indent=indent
        )

    # ---- intent-failure localization ------------------------------------
    def divergence_stages(self) -> list[StageName]:
        """Stages Reflection blamed (non-SHIP routing), in order seen."""
        blamed: list[StageName] = []
        for r in self.records:
            if r.stage != StageName.REFLECTION:
                continue
            target = r.outputs.get("routing_target")
            try:
                rt = RoutingTarget(target)
            except (ValueError, TypeError):
                continue
            stage = _BLAME_STAGE.get(rt)
            if stage is not None:
                blamed.append(stage)
        return blamed

    def intent_timeline_callout(self) -> str:
        """A collapsed Obsidian callout marking where intent diverged."""
        blamed = set(self.divergence_stages())
        lines = ["> [!info]- Intent timeline",
                 "> Each stage's understanding of the request. "
                 "⚠ marks a stage Reflection blamed for an intent/strategy miss."]
        for r in self.records:
            mark = "⚠ " if r.stage in blamed else ""
            llm = r.llm_used or "—"
            lines.append(
                f"> - {mark}**{r.stage.value}** (attempt {r.attempt}, "
                f"conf {r.confidence:.2f}, {llm}): {r.intent_understanding}"
            )
        return "\n".join(lines)
