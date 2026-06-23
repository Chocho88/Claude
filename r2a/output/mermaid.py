"""Mermaid helpers. Mermaid is literal text in a fenced block — no runtime dep."""

from __future__ import annotations

from r2a.domain.synthesis import SynthesisOutput


def fence(body: str) -> str:
    return f"```mermaid\n{body.strip()}\n```"


def _san(text: str, n: int = 40) -> str:
    """Make a label safe for a mermaid node."""
    t = text.replace('"', "'").replace("\n", " ").strip()
    return (t[:n] + "…") if len(t) > n else t


def concept_map(draft: SynthesisOutput) -> str:
    """A simple flowchart linking the deliverable to the bites it cites."""
    lines = ["flowchart TD", f'  ROOT["{_san(draft.title, 30)}"]']
    for i, item in enumerate(draft.items[:8]):
        node = f"I{i}"
        lines.append(f'  ROOT --> {node}["{_san(item.text)}"]')
        for cite in item.cites[:2]:
            lines.append(f'  {node} -.cites.-> B_{i}_{cite[:8]}(["{cite}"])')
    return fence("\n".join(lines))
