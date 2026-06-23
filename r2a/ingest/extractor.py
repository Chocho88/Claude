"""Extract atomic knowledge bites from passages via the LLM.

Per-passage extraction keeps context bounded. Each draft is checked against its
passage (fuzzy verbatim) so `location` stays re-locatable and citations remain
checkable; a poor match lowers the bite's confidence rather than being dropped
outright. When the model returns nothing (e.g. the offline stub), we fall back to
one bite per passage so ingest always yields a citable corpus.
"""

from __future__ import annotations

import hashlib
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from r2a.adapters.llm.base import LLMProvider
from r2a.domain.bite import BiteType, KnowledgeBite
from r2a.domain.common import Msg

from .chunker import Passage
from .loaders import DocMeta

_SYSTEM = (
    "You are the extraction stage. From the passage, extract atomic knowledge "
    "bites — each a single claim, definition, statistic, or example. Use the "
    "author's wording verbatim where possible. Do not invent content; if the "
    "passage has none, return an empty list."
)


class BiteDraft(BaseModel):
    text: str
    type: BiteType = BiteType.CLAIM
    confidence: float = 0.8


class ExtractionResult(BaseModel):
    bites: list[BiteDraft] = Field(default_factory=list)


def _bite_id(namespace: str, passage_index: int, text: str) -> str:
    h = hashlib.sha1(f"{namespace}|{passage_index}|{text}".encode()).hexdigest()[:12]
    return f"{namespace}:{h}"


def _verbatim_score(bite_text: str, passage_text: str) -> float:
    """How well the bite text is grounded in the passage (0..1)."""
    return SequenceMatcher(None, bite_text.lower(), passage_text.lower()).ratio()


def extract_bites(
    passages: list[Passage],
    meta: DocMeta,
    llm: LLMProvider,
    *,
    namespace: str,
    max_tokens: int = 1200,
) -> list[KnowledgeBite]:
    bites: list[KnowledgeBite] = []
    for passage in passages:
        result = llm.complete_json(
            system=_SYSTEM,
            messages=[Msg(role="user", content=passage.text)],
            schema=ExtractionResult,
            max_tokens=max_tokens,
        )
        drafts = result.bites
        if not drafts:
            # Fallback: treat the passage itself as one bite.
            drafts = [BiteDraft(text=passage.text[:500], confidence=0.4)]

        for draft in drafts:
            text = draft.text.strip()
            if not text:
                continue
            # Ground the confidence in how verbatim the bite is.
            grounding = _verbatim_score(text, passage.text)
            confidence = round(min(draft.confidence, 0.3 + 0.7 * grounding), 3)
            bites.append(
                KnowledgeBite(
                    id=_bite_id(namespace, passage.index, text),
                    text=text,
                    type=draft.type,
                    source_title=meta.title,
                    author=meta.author,
                    location=passage.location,
                    namespace=namespace,
                    confidence=confidence,
                )
            )
    return bites
