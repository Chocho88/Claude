"""Job + elicitation answers — the unit of work flowing through the queue."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .artifact import ArtifactType
from .common import utcnow
from .plan import Scope, TaskType


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_INPUT = "needs_input"  # Planning asked follow-ups; awaiting answers
    DONE = "done"
    FAILED = "failed"


class Constraints(BaseModel):
    count: int | None = None  # e.g. "give me 5 ideas"
    length: str | None = None  # e.g. "short", "1 page"
    audience: str | None = None
    artifacts: list[ArtifactType] = Field(
        default_factory=lambda: [ArtifactType.HUB]
    )


class ElicitationAnswers(BaseModel):
    """The user's tappable answers plus their original free-text request."""

    raw_request: str = ""  # the user's own words; the anchor for intent checks
    scope: Scope = Scope.IMPORT
    task: TaskType = TaskType.SUMMARIZE
    constraints: Constraints = Field(default_factory=Constraints)
    followups: dict[str, str] = Field(default_factory=dict)  # question id -> answer
    free_text: str | None = None  # "other" escape hatch


class JobResult(BaseModel):
    hub_note_path: str | None = None
    trace_path: str | None = None
    artifact_paths: list[str] = Field(default_factory=list)
    shipped_with_caveat: bool = False
    error: str | None = None


class Job(BaseModel):
    """A single import-to-artifact request."""

    id: str
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    source_paths: list[str] = Field(default_factory=list)  # docs to ingest
    namespaces: list[str] = Field(default_factory=list)  # already-ingested ids
    answers: ElicitationAnswers = Field(default_factory=ElicitationAnswers)
    output_dir: str = ""  # vault subpath for this job's artifacts
    result: JobResult | None = None

    def touch(self) -> None:
        self.updated_at = utcnow()
