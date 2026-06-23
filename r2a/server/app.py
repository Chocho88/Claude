"""FastAPI app: submit jobs, run the tappable elicitation, read results.

Endpoints (all under /api):
  GET  /api/meta              vocabulary + current privacy/LLM state for the UI
  POST /api/jobs              submit a job (paste text or point at a path)
  GET  /api/jobs              list jobs across all queue states
  GET  /api/jobs/{id}         one job + result, or its follow-up questions
  POST /api/jobs/{id}/answers answer Planning's adaptive follow-ups, re-queue
  GET  /api/jobs/{id}/artifact?path=...   fetch a produced artifact file

The PWA in web/ is served at /. A single background worker drains the queue
(single-writer discipline); disable it with autodrain=False to drive draining
deterministically from tests.
"""

from __future__ import annotations

import os
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from r2a import __version__
from r2a.config import Config
from r2a.domain.artifact import ArtifactType
from r2a.domain.job import Constraints, ElicitationAnswers, Job
from r2a.domain.plan import Scope, TaskType
from r2a.queue.folder_queue import FolderJobQueue
from r2a.runner import drain_forever

WEB_DIR = Path(__file__).resolve().parents[2] / "web"


# --- request/response models ----------------------------------------------


class CoreOption(BaseModel):
    value: str
    label: str
    note: str | None = None


class CoreQuestion(BaseModel):
    id: str
    text: str
    kind: str  # single | multi
    options: list[CoreOption]


class Meta(BaseModel):
    version: str
    llm_name: str
    routing: str
    claude_available: bool
    core_questions: list[CoreQuestion]


class JobCreate(BaseModel):
    raw_request: str = ""
    task: TaskType = TaskType.IDEAS
    scope: Scope = Scope.IMPORT
    artifacts: list[ArtifactType] = Field(default_factory=lambda: [ArtifactType.HUB])
    count: int | None = None
    audience: str | None = None
    text: str | None = None  # pasted content
    source_path: str | None = None  # an existing file on the Mac


class AnswersIn(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


# --- vocabulary for the tappable core (each option changes the work) -------

_CORE_QUESTIONS = [
    CoreQuestion(
        id="task", text="What should I make from this?", kind="single",
        options=[
            CoreOption(value="ideas", label="Ideas", note="product/feature ideas"),
            CoreOption(value="org_habit", label="Org & habits"),
            CoreOption(value="insights", label="Insights"),
            CoreOption(value="analyze", label="Analyze"),
            CoreOption(value="compare", label="Compare"),
            CoreOption(value="summarize", label="Summarize"),
        ],
    ),
    CoreQuestion(
        id="scope", text="How far beyond the source may I reach?", kind="single",
        options=[
            CoreOption(value="import", label="Just the import",
                       note="stays on device"),
            CoreOption(value="import_model", label="+ model knowledge",
                       note="may use Claude"),
            CoreOption(value="import_web", label="+ web",
                       note="content leaves the device"),
        ],
    ),
    CoreQuestion(
        id="artifacts", text="Which artifacts?", kind="multi",
        options=[
            CoreOption(value="hub", label="Hub note"),
            CoreOption(value="mermaid", label="Diagram"),
            CoreOption(value="deck", label="Slide deck"),
            CoreOption(value="html", label="Prototype"),
        ],
    ),
]


def _job_view(state: str, payload: dict) -> dict:
    """Trim a stored job payload to what the UI needs."""
    return {
        "id": payload.get("id"),
        "status": state,
        "task": payload.get("answers", {}).get("task"),
        "scope": payload.get("answers", {}).get("scope"),
        "raw_request": payload.get("answers", {}).get("raw_request", ""),
        "result": payload.get("result"),
        "followups": payload.get("followups", []),
    }


def create_app(config: Config | None = None, *, autodrain: bool = True) -> FastAPI:
    cfg = config or Config.load(os.environ.get("R2A_CONFIG"))
    queue = FolderJobQueue(cfg.paths.queue())
    inbox = cfg.paths.root() / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    stop = threading.Event()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        worker: threading.Thread | None = None
        if autodrain:
            worker = threading.Thread(
                target=drain_forever, args=(cfg, stop), daemon=True
            )
            worker.start()
        try:
            yield
        finally:
            stop.set()
            if worker is not None:
                worker.join(timeout=2.0)

    app = FastAPI(title="Research to Artifact", version=__version__, lifespan=lifespan)

    def _privacy_state() -> tuple[str, bool]:
        from r2a.factory import default_llm

        llm = default_llm(cfg)
        return llm.name, bool(os.environ.get("ANTHROPIC_API_KEY"))

    @app.get("/api/meta", response_model=Meta)
    def meta() -> Meta:
        llm_name, claude_available = _privacy_state()
        return Meta(
            version=__version__,
            llm_name=llm_name,
            routing=cfg.llm.routing,
            claude_available=claude_available,
            core_questions=_CORE_QUESTIONS,
        )

    @app.post("/api/jobs")
    def create_job(body: JobCreate) -> dict:
        job_id = uuid.uuid4().hex[:12]
        source_paths: list[str] = []
        if body.source_path:
            p = Path(body.source_path).expanduser()
            if not p.exists():
                raise HTTPException(400, f"source_path not found: {body.source_path}")
            source_paths.append(str(p))
        elif body.text and body.text.strip():
            doc = inbox / f"{job_id}.md"
            doc.write_text(body.text, encoding="utf-8")
            source_paths.append(str(doc))
        else:
            raise HTTPException(400, "provide either text or source_path")

        artifacts = body.artifacts or [ArtifactType.HUB]
        if ArtifactType.HUB not in artifacts:
            artifacts = [ArtifactType.HUB, *artifacts]
        request = body.raw_request.strip() or f"{body.task.value} from the import"
        job = Job(
            id=job_id,
            source_paths=source_paths,
            answers=ElicitationAnswers(
                raw_request=request,
                task=body.task,
                scope=body.scope,
                constraints=Constraints(
                    count=body.count, audience=body.audience, artifacts=artifacts
                ),
            ),
        )
        queue.enqueue(job)
        return {"id": job.id, "status": "queued"}

    @app.get("/api/jobs")
    def list_jobs() -> list[dict]:
        return [_job_view(state, payload) for state, payload in queue.list_jobs()]

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict:
        rec = queue.read(job_id)
        if rec is None:
            raise HTTPException(404, "job not found")
        return _job_view(*rec)

    @app.post("/api/jobs/{job_id}/answers")
    def answer_job(job_id: str, body: AnswersIn) -> dict:
        job = queue.submit_answers(job_id, body.answers)
        if job is None:
            raise HTTPException(409, "job is not awaiting answers")
        return {"id": job.id, "status": "queued"}

    @app.get("/api/jobs/{job_id}/artifact")
    def get_artifact(path: str) -> FileResponse:
        target = Path(path).expanduser().resolve()
        vault = cfg.paths.vault().resolve()
        if vault not in target.parents and target != vault:
            raise HTTPException(403, "outside the vault")
        if not target.is_file():
            raise HTTPException(404, "artifact not found")
        return FileResponse(target)

    if WEB_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
    else:  # engine still usable without the front-end bundle
        @app.get("/")
        def _no_web() -> JSONResponse:
            return JSONResponse({"detail": "web/ not found; API only"}, status_code=200)

    return app
