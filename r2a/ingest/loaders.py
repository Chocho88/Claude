"""Load a document path into raw text + metadata, dispatched by extension."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .parsers import parse_docx, parse_md, parse_pdf, parse_txt

# Form-feed separates PDF pages so the chunker can recover page locations.
PAGE_SEP = "\f"


class DocMeta(BaseModel):
    title: str
    author: str | None = None
    source_path: str
    ext: str  # "md" | "pdf" | "docx" | "txt"
    n_chars: int = 0


_PARSERS = {
    ".md": ("md", parse_md),
    ".markdown": ("md", parse_md),
    ".txt": ("txt", parse_txt),
    ".text": ("txt", parse_txt),
    ".pdf": ("pdf", parse_pdf),
    ".docx": ("docx", parse_docx),
}


def load_document(path: str | Path) -> tuple[str, DocMeta]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    entry = _PARSERS.get(p.suffix.lower())
    if entry is None:
        raise ValueError(
            f"Unsupported file type {p.suffix!r}; supported: "
            f"{sorted({e[0] for e in _PARSERS.values()})}"
        )
    ext, parser = entry
    text, author = parser(p)
    meta = DocMeta(
        title=p.stem,
        author=author,
        source_path=str(p),
        ext=ext,
        n_chars=len(text),
    )
    return text, meta
