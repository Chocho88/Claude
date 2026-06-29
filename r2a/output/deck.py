"""Render a clean Markdown slide deck in Obsidian Slides format.

Slides are separated by `---` on their own line, so the file reads as a normal
note *and* presents as slides via Obsidian's Slides core plugin. Tone is
deliberately human and spare — no emoji, no "In conclusion", short bullets.
"""

from __future__ import annotations

from r2a.pipeline.stage import StageContext

from . import mermaid

_PER_SLIDE = 4


def _source_title(ctx: StageContext) -> str:
    return ctx.retrieved[0].bite.source_title if ctx.retrieved else "the import"


def _heading(ctx: StageContext) -> str:
    task = ctx.plan.task.value if ctx.plan else "notes"
    return {
        "ideas": "Ideas",
        "insights": "Insights",
        "analyze": "Analysis",
        "compare": "Comparison",
        "summarize": "Summary",
        "org_habit": "Habits",
    }.get(task, "Highlights")


def render_deck(ctx: StageContext) -> str:
    draft = ctx.draft
    assert draft is not None
    src = _source_title(ctx)
    slides: list[str] = []

    # Title slide.
    slides.append(f"# {draft.title}\n\nFrom *{src}*")

    if draft.summary:
        slides.append(f"## Overview\n\n{draft.summary}")

    # Content slides — a few bullets each, footnoted with the source.
    heading = _heading(ctx)
    items = draft.items
    for start in range(0, len(items), _PER_SLIDE):
        chunk = items[start : start + _PER_SLIDE]
        lines = [f"## {heading}"]
        for item in chunk:
            tag = " *(derived)*" if item.derived else ""
            tag += " `[model knowledge]`" if item.model_knowledge else ""
            lines.append(f"- {item.text}{tag}")
        slides.append("\n".join(lines))

    if draft.mermaid:
        slides.append("## Concept map\n\n" + mermaid.fence(draft.mermaid))
    elif items:
        slides.append("## Concept map\n\n" + mermaid.concept_map(draft))

    slides.append(
        f"## Source\n\n{src}\n\nFull citations and the agent trace are in the hub note."
    )

    frontmatter = "\n".join([
        "---",
        f"title: {draft.title} — deck",
        "tags: [research-to-artifact, deck]",
        "---",
        "",
    ])
    return frontmatter + "\n\n---\n\n".join(slides) + "\n"
