"""Structure-aware chunking into bounded passages with a recoverable location.

Markdown splits on headings (location = current heading); PDF splits on page
breaks (location = page N); txt/docx split on blank lines. Each section is then
packed into passages of at most `max_chars` so extraction sees bounded context.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from .parsers import PAGE_SEP

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


class Passage(BaseModel):
    text: str
    location: str | None = None  # heading / "p3"
    index: int


def _pack(text: str, location: str | None, max_chars: int) -> list[tuple[str, str | None]]:
    """Split one section into <= max_chars pieces on paragraph boundaries."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out: list[tuple[str, str | None]] = []
    buf = ""
    for para in paras:
        if buf and len(buf) + len(para) + 2 > max_chars:
            out.append((buf, location))
            buf = ""
        # A single oversized paragraph is emitted on its own (hard-split).
        if len(para) > max_chars:
            if buf:
                out.append((buf, location))
                buf = ""
            for i in range(0, len(para), max_chars):
                out.append((para[i : i + max_chars], location))
            continue
        buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        out.append((buf, location))
    return out


def _sections(text: str, ext: str) -> list[tuple[str, str | None]]:
    """Split into (section_text, location) by document structure."""
    if ext == "pdf":
        return [
            (page, f"p{i + 1}")
            for i, page in enumerate(text.split(PAGE_SEP))
            if page.strip()
        ]
    if ext == "md":
        sections: list[tuple[str, str | None]] = []
        current_heading: str | None = None
        body: list[str] = []
        for line in text.splitlines():
            m = _HEADING.match(line)
            if m:
                if body:
                    sections.append(("\n".join(body), current_heading))
                    body = []
                current_heading = m.group(2).strip()
            else:
                body.append(line)
        if body:
            sections.append(("\n".join(body), current_heading))
        return [(t, loc) for t, loc in sections if t.strip()]
    # txt / docx: one big section, packed by paragraphs below.
    return [(text, None)]


def chunk_text(text: str, ext: str, *, max_chars: int = 1200) -> list[Passage]:
    passages: list[Passage] = []
    for section_text, location in _sections(text, ext):
        for piece, loc in _pack(section_text, location, max_chars):
            passages.append(
                Passage(text=piece.strip(), location=loc, index=len(passages))
            )
    return passages
