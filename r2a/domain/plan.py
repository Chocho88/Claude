"""Scope/task vocabulary and the Planning stage's output."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .common import Question


class Scope(str, Enum):
    """How far beyond the import the system may reach."""

    IMPORT = "import"  # just the imported content
    IMPORT_MODEL = "import_model"  # + the model's own knowledge
    IMPORT_WEB = "import_web"  # + web search (content leaves the device)


class TaskType(str, Enum):
    IDEAS = "ideas"
    ORG_HABIT = "org_habit"
    INSIGHTS = "insights"
    ANALYZE = "analyze"
    COMPARE = "compare"
    SUMMARIZE = "summarize"


class PlanSpec(BaseModel):
    """The plan that drives Retrieval and Synthesis.

    If the request is underspecified, Planning sets `needs_input=True` and
    populates `followup_questions`; the orchestrator then pauses the job for
    answers rather than guessing.
    """

    intent: str  # restatement of what the user wants
    scope: Scope
    task: TaskType
    strategy: str = ""  # how the system will approach it
    answer_shape: str = ""  # the planned deliverable shape
    top_k: int = 8
    needs_input: bool = False
    followup_questions: list[Question] = Field(default_factory=list)
