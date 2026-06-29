"""r2a CLI: ingest, enqueue, worker, run, info."""

from __future__ import annotations

import uuid
from pathlib import Path

import typer

from r2a import __version__
from r2a.config import Config
from r2a.domain.artifact import ArtifactType
from r2a.domain.job import Constraints, ElicitationAnswers, Job
from r2a.domain.plan import Scope, TaskType
from r2a.factory import build_deps
from r2a.queue.folder_queue import FolderJobQueue
from r2a.runner import drain_queue, process_job

app = typer.Typer(help="Research to Artifact — local-first agentic knowledge app.")


def _config(config_path: str | None) -> Config:
    return Config.load(config_path)


def _parse_artifacts(spec: str) -> list[ArtifactType]:
    out = [ArtifactType.HUB]
    for token in (t.strip() for t in spec.split(",") if t.strip()):
        try:
            a = ArtifactType(token)
        except ValueError:
            raise typer.BadParameter(f"unknown artifact {token!r}")
        if a not in out:
            out.append(a)
    return out


def _build_job(source, task, scope, artifacts, count, audience, request) -> Job:
    answers = ElicitationAnswers(
        raw_request=request or f"{task} from {Path(source).name}",
        task=TaskType(task),
        scope=Scope(scope),
        constraints=Constraints(
            count=count, audience=audience, artifacts=_parse_artifacts(artifacts)
        ),
    )
    return Job(id=uuid.uuid4().hex[:12], source_paths=[str(source)], answers=answers)


@app.command()
def info(config_path: str = typer.Option(None, "--config", help="TOML config")) -> None:
    """Show the active configuration and which adapters are wired."""
    cfg = _config(config_path)
    deps = build_deps(cfg)
    typer.echo(f"research-to-artifact {__version__}")
    typer.echo(f"  llm      : {deps.llm.name}  (routing={cfg.llm.routing})")
    typer.echo(f"  embedder : {deps.embedder.model_id}")
    typer.echo(f"  store    : {type(deps.store).__name__}")
    typer.echo(f"  workspace: {cfg.paths.root()}")


@app.command()
def ingest(
    path: str,
    config_path: str = typer.Option(None, "--config"),
) -> None:
    """Ingest a document into the vector store and print its namespace."""
    cfg = _config(config_path)
    deps = build_deps(cfg)
    from r2a.ingest import ingest_document

    res = ingest_document(path, embedder=deps.embedder, store=deps.store, llm=deps.llm)
    typer.echo(f"ingested {res.source_title}")
    typer.echo(f"  namespace : {res.namespace}")
    typer.echo(f"  passages  : {res.n_passages}")
    typer.echo(f"  bites     : {res.n_bites}")


@app.command()
def enqueue(
    source: str,
    task: str = typer.Option("ideas", help="ideas|org_habit|insights|analyze|compare|summarize"),
    scope: str = typer.Option("import", help="import|import_model|import_web"),
    artifacts: str = typer.Option("hub,mermaid", help="comma list: hub,mermaid,html,deck"),
    count: int = typer.Option(None),
    audience: str = typer.Option(None),
    request: str = typer.Option(None, help="the user's own words"),
    config_path: str = typer.Option(None, "--config"),
) -> None:
    """Drop a job file into the queue (what the iPhone client does)."""
    cfg = _config(config_path)
    job = _build_job(source, task, scope, artifacts, count, audience, request)
    FolderJobQueue(cfg.paths.queue()).enqueue(job)
    typer.echo(f"queued job {job.id}  ({cfg.paths.queue()})")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="bind address (use 0.0.0.0 for LAN/iPhone)"),
    port: int = typer.Option(8765),
    config_path: str = typer.Option(None, "--config"),
) -> None:
    """Serve the local web app + PWA, with a background worker draining the queue."""
    import os

    import uvicorn

    if config_path:
        os.environ["R2A_CONFIG"] = config_path
    cfg = _config(config_path)
    typer.echo(f"serving http://{host}:{port}  (vault={cfg.paths.vault()})")
    uvicorn.run("r2a.server.app:create_app", factory=True, host=host, port=port)


@app.command()
def worker(config_path: str = typer.Option(None, "--config")) -> None:
    """Drain the queue: claim each job, run it, write artifacts to the vault."""
    cfg = _config(config_path)
    results = drain_queue(cfg)
    if not results:
        typer.echo("no queued jobs")
        return
    for job_id, status in results:
        typer.echo(f"  {job_id}: {status}")


@app.command()
def run(
    source: str,
    task: str = typer.Option("ideas"),
    scope: str = typer.Option("import"),
    artifacts: str = typer.Option("hub,mermaid,deck"),
    count: int = typer.Option(None),
    audience: str = typer.Option(None),
    request: str = typer.Option(None),
    config_path: str = typer.Option(None, "--config"),
) -> None:
    """Ingest + run one job immediately and print where the artifacts landed."""
    cfg = _config(config_path)
    job = _build_job(source, task, scope, artifacts, count, audience, request)
    deps = build_deps(cfg)
    result = process_job(job, deps, cfg)
    if result.status.value == "needs_input":
        typer.echo("needs input — Planning asked follow-up questions:")
        for q in result.followups or []:
            typer.echo(f"  - {q.text}")
        return
    r = result.result
    typer.echo(f"done{'  (shipped with caveat)' if result.ship_with_caveat else ''}")
    typer.echo(f"  hub   : {r.hub_note_path}")
    for p in r.artifact_paths[1:]:
        typer.echo(f"  art   : {p}")
    typer.echo(f"  trace : {r.trace_path}")


if __name__ == "__main__":
    app()
