"""M4: folder job queue mechanics + end-to-end drain + CLI smoke."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from r2a.cli import app
from r2a.config import Config, PathsConfig
from r2a.domain.artifact import ArtifactType
from r2a.domain.job import Constraints, ElicitationAnswers, Job, JobResult, JobStatus
from r2a.domain.plan import Scope, TaskType
from r2a.queue.folder_queue import FolderJobQueue
from r2a.runner import drain_queue

_DOC = (
    "# Healthier social apps\n"
    "## Contextual trust\nContextual trust is scoped to a person and a situation.\n\n"
    "## Live experiences\nSynchronous co-presence beats broadcasting.\n"
)


def _job(source=None):
    answers = ElicitationAnswers(
        raw_request="ideas for healthier sharing",
        task=TaskType.IDEAS,
        scope=Scope.IMPORT,
        constraints=Constraints(artifacts=[ArtifactType.HUB, ArtifactType.DECK]),
    )
    return Job(id="job-a", source_paths=[source] if source else [], answers=answers)


def test_claim_complete_lifecycle(tmp_path):
    q = FolderJobQueue(tmp_path / "queue")
    q.enqueue(_job())

    claimed = q.claim_next()
    assert claimed is not None and claimed.status == JobStatus.RUNNING
    assert (tmp_path / "queue" / "running" / "job-a.json").exists()

    q.complete(claimed, JobResult(hub_note_path="x.md"))
    assert (tmp_path / "queue" / "done" / "job-a.json").exists()
    assert not (tmp_path / "queue" / "running" / "job-a.json").exists()
    assert q.claim_next() is None  # queue now empty


def test_claim_is_atomic_single_winner(tmp_path):
    q = FolderJobQueue(tmp_path / "queue")
    q.enqueue(_job())
    first = q.claim_next()
    second = q.claim_next()
    assert first is not None and second is None  # claimed exactly once


def test_fail_routes_to_failed(tmp_path):
    q = FolderJobQueue(tmp_path / "queue")
    q.enqueue(_job())
    job = q.claim_next()
    q.fail(job, "boom")
    assert (tmp_path / "queue" / "failed" / "job-a.json").exists()


def _config(tmp_path) -> Config:
    return Config(paths=PathsConfig(workspace=str(tmp_path / "ws")))


def test_drain_queue_end_to_end(tmp_path):
    cfg = _config(tmp_path)
    doc = tmp_path / "social.md"
    doc.write_text(_DOC, encoding="utf-8")

    FolderJobQueue(cfg.paths.queue()).enqueue(_job(source=str(doc)))
    results = drain_queue(cfg)

    assert results == [("job-a", "done")]
    out_dir = cfg.paths.vault() / "job-a"
    assert (out_dir / "trace.json").exists()
    assert any(out_dir.glob("*.md"))  # hub note
    assert any(out_dir.glob("*-deck.md"))  # requested deck artifact


def test_cli_run_smoke(tmp_path):
    cfg_toml = tmp_path / "config.toml"
    cfg_toml.write_text(f'[paths]\nworkspace = "{tmp_path / "ws"}"\n', encoding="utf-8")
    doc = tmp_path / "doc.md"
    doc.write_text(_DOC, encoding="utf-8")

    result = CliRunner().invoke(
        app, ["run", str(doc), "--task", "ideas", "--config", str(cfg_toml)]
    )
    assert result.exit_code == 0, result.output
    assert "hub" in result.output and "done" in result.output
