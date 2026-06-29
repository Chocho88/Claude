"""Swappable I/O behind interfaces.

`*/base.py` holds the ABCs that domain/ and pipeline/ may import. Concrete
implementations (claude, sbert, lancedb, and their stub doubles) are wired only
at the edges (factory, CLI, test fixtures). The import-linter contract in
pyproject.toml enforces that domain/pipeline never import a concrete.
"""
