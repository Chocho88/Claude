"""Per-format text extractors. Heavy deps (pypdf, python-docx) imported lazily.

Each parser returns (text, author|None). PDF pages are joined with a form-feed
so the chunker can recover page numbers.
"""

from __future__ import annotations

from pathlib import Path

PAGE_SEP = "\f"


def parse_txt(path: Path) -> tuple[str, None]:
    return path.read_text(encoding="utf-8", errors="replace"), None


def parse_md(path: Path) -> tuple[str, None]:
    # Markdown is kept as raw text; the chunker reads its heading structure.
    return path.read_text(encoding="utf-8", errors="replace"), None


def parse_pdf(path: Path) -> tuple[str, str | None]:
    try:
        from pypdf import PdfReader
    except ImportError as e:  # pragma: no cover - exercised only without extra
        raise ImportError("PDF support needs the 'ingest' extra: pip install -e '.[ingest]'") from e

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    author = None
    if reader.metadata:
        author = reader.metadata.author or None
    return PAGE_SEP.join(pages), author


def parse_docx(path: Path) -> tuple[str, str | None]:
    try:
        import docx  # python-docx
    except ImportError as e:  # pragma: no cover
        raise ImportError("DOCX support needs the 'ingest' extra: pip install -e '.[ingest]'") from e

    document = docx.Document(str(path))
    text = "\n\n".join(p.text for p in document.paragraphs if p.text.strip())
    author = None
    try:
        author = document.core_properties.author or None
    except Exception:
        pass
    return text, author
