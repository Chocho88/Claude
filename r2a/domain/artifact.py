"""Artifact types the pipeline can produce."""

from __future__ import annotations

from enum import Enum


class ArtifactType(str, Enum):
    HUB = "hub"  # the Markdown hub note (always produced)
    MERMAID = "mermaid"  # mermaid flowchart / concept map (inline in the hub)
    HTML = "html"  # standalone interactive prototype
    DECK = "deck"  # Obsidian-Slides Markdown deck
