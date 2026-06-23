"""Render the Obsidian hub note: frontmatter, cited items, mermaid, intent timeline."""

from __future__ import annotations

from r2a.domain.common import utcnow
from r2a.domain.synthesis import SynthItem
from r2a.pipeline.stage import StageContext
from r2a.pipeline.tracer import Tracer

from . import mermaid


def _frontmatter(ctx: StageContext) -> str:
    source = ctx.retrieved[0].bite.source_title if ctx.retrieved else "import"
    author = ctx.retrieved[0].bite.author if ctx.retrieved else None
    plan = ctx.plan
    tags = ["research-to-artifact"]
    if plan:
        tags.append(plan.task.value)
    fm = [
        "---",
        f"title: {ctx.draft.title if ctx.draft else 'Artifact'}",
        f"source: {source}",
        f"author: {author or ''}",
        f"created: {utcnow().date().isoformat()}",
        f"type: {plan.task.value if plan else 'artifact'}",
        f"scope: {plan.scope.value if plan else 'import'}",
        f"tags: [{', '.join(tags)}]",
        "---",
    ]
    return "\n".join(fm)


def _cite_links(item: SynthItem, ctx: StageContext) -> str:
    """Render an item's citations as Obsidian wikilinks (graph nodes)."""
    by_id = {sb.bite.id: sb.bite for sb in ctx.retrieved}
    parts = []
    for cid in item.cites:
        b = by_id.get(cid)
        if b is None:
            parts.append(f"[[{cid}]]")
        elif b.location:
            parts.append(f"[[{b.source_title}#{b.location}|{cid}]]")
        else:
            parts.append(f"[[{b.source_title}|{cid}]]")
    flags = []
    if item.derived:
        flags.append("_derived_")
    if item.model_knowledge:
        flags.append("`[model knowledge]`")
    for w in item.web_sources:
        flags.append(f"[web]({w})")
    tail = (" — " + ", ".join(parts)) if parts else ""
    if flags:
        tail += " " + " ".join(flags)
    return tail


def _artifact_links(links: dict[str, str]) -> list[str]:
    """Render an Artifacts section linking the deck (wikilink) and HTML (path)."""
    if not links:
        return []
    out = ["## Artifacts", ""]
    if "deck" in links:
        # Strip .md for the Obsidian wikilink.
        name = links["deck"].rsplit(".md", 1)[0]
        out.append(f"- Slide deck: [[{name}]]")
    if "html" in links:
        out.append(f"- Interactive prototype: [{links['html']}]({links['html']})")
    out.append("")
    return out


def render_hub_note(
    ctx: StageContext, tracer: Tracer, links: dict[str, str] | None = None
) -> str:
    draft = ctx.draft
    assert draft is not None
    out: list[str] = [_frontmatter(ctx), ""]

    if ctx.ship_with_caveat:
        out += [
            "> [!warning] Shipped with caveat",
            "> The reflection loop exhausted its budget before fully passing. "
            "This is the best-scoring draft; see the intent timeline below.",
            "",
        ]

    out += [f"# {draft.title}", ""]
    if draft.summary:
        out += [draft.summary, ""]

    out += ["## Items", ""]
    for item in draft.items:
        out.append(f"- {item.text}{_cite_links(item, ctx)}")
    out.append("")

    if draft.mermaid:
        out += ["## Concept map", "", mermaid.fence(draft.mermaid), ""]
    elif draft.items:
        out += ["## Concept map", "", mermaid.concept_map(draft), ""]

    out += _artifact_links(links or {})

    # Human-readable intent-failure localization.
    out += [tracer.intent_timeline_callout(), ""]
    out += [
        "> [!note]- Agent trace",
        "> Full machine-readable trace saved beside this note as `trace.json`.",
        "",
    ]
    return "\n".join(out)
