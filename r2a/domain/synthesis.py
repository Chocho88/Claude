"""The deliverable produced by Synthesis."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SynthItem(BaseModel):
    """One unit of the deliverable (an idea, insight, finding, ...).

    Fidelity rule: `cites` lists the source bite ids this item derives from.
    `derived=True` flags content that goes beyond the source; `model_knowledge`
    flags content labelled `[model knowledge]`; `web_sources` cites the web.
    """

    text: str
    cites: list[str] = Field(default_factory=list)  # source bite ids
    derived: bool = False
    model_knowledge: bool = False
    web_sources: list[str] = Field(default_factory=list)


class SynthesisOutput(BaseModel):
    """A complete draft; the best-scoring one across loop attempts is shipped."""

    title: str
    summary: str = ""
    items: list[SynthItem] = Field(default_factory=list)
    mermaid: str | None = None  # fenced mermaid block body (no fences)
    score: int = 0  # filled in by Reflection so best_draft can be tracked

    def cited_bite_ids(self) -> set[str]:
        ids: set[str] = set()
        for item in self.items:
            ids.update(item.cites)
        return ids
