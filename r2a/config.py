"""Configuration: code defaults, optionally overlaid from a TOML file.

Kept as plain pydantic models (not env-driven settings) so it's trivial to
construct in tests and to serialise into the trace.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    workspace: str = "./scratch/workspace"
    vault_subdir: str = "vault"
    store_subdir: str = "vector_store"
    queue_subdir: str = "queue"

    def root(self) -> Path:
        return Path(self.workspace).expanduser()

    def vault(self) -> Path:
        return self.root() / self.vault_subdir

    def store(self) -> Path:
        return self.root() / self.store_subdir

    def queue(self) -> Path:
        return self.root() / self.queue_subdir


class LLMConfig(BaseModel):
    routing: str = "auto"  # auto | force_local | force_claude
    claude_model: str = "claude-sonnet-4-6"
    fallback_confidence: float = 0.55


class EmbeddingConfig(BaseModel):
    model_id: str = "BAAI/bge-small-en-v1.5"


class RetrievalConfig(BaseModel):
    top_k: int = 8


class LoopConfig(BaseModel):
    max_synth_per_phase: int = 3  # 1 initial + up to 2 re-synth from same bites
    max_escalations: int = 1


class Config(BaseModel):
    paths: PathsConfig = Field(default_factory=PathsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    loop: LoopConfig = Field(default_factory=LoopConfig)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        """Load defaults, overlaid by a TOML file if one is given/exists."""
        if path is None:
            return cls()
        p = Path(path)
        if not p.exists():
            return cls()
        with p.open("rb") as fh:
            data = tomllib.load(fh)
        return cls.model_validate(data)
