"""Structure-aware chunking: headings, pages, and size bounding."""

from __future__ import annotations

from r2a.ingest.chunker import chunk_text
from r2a.ingest.parsers import PAGE_SEP


def test_markdown_splits_on_headings_with_locations():
    md = (
        "# Intro\nSome opening text.\n\n"
        "## Trust\nContextual trust is situational.\n\n"
        "## Sharing\nLive experiences beat broadcasting.\n"
    )
    passages = chunk_text(md, "md")
    locs = [p.location for p in passages]
    assert "Intro" in locs and "Trust" in locs and "Sharing" in locs
    trust = next(p for p in passages if p.location == "Trust")
    assert "situational" in trust.text


def test_pdf_splits_on_pages():
    text = f"page one body{PAGE_SEP}page two body{PAGE_SEP}page three"
    passages = chunk_text(text, "pdf")
    assert [p.location for p in passages] == ["p1", "p2", "p3"]


def test_long_section_is_size_bounded():
    para = "word " * 600  # ~3000 chars, one paragraph
    passages = chunk_text(para, "txt", max_chars=1000)
    assert len(passages) >= 3
    assert all(len(p.text) <= 1000 for p in passages)


def test_indices_are_sequential():
    passages = chunk_text("a\n\nb\n\nc", "txt", max_chars=1)
    assert [p.index for p in passages] == list(range(len(passages)))
