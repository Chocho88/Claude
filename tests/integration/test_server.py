"""Server slice: submit → drain → results, the answer flow, and path safety.

All offline: the app's factory wires the StubProvider (no API key) + HashEmbedder,
and we drive the worker deterministically with drain_queue (autodrain off).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from r2a.config import Config, PathsConfig
from r2a.domain.common import Question
from r2a.domain.job import ElicitationAnswers, Job
from r2a.queue.folder_queue import FolderJobQueue
from r2a.runner import drain_queue
from r2a.server.app import create_app


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    return Config(paths=PathsConfig(workspace=str(tmp_path / "ws")))


@pytest.fixture
def client(cfg: Config) -> TestClient:
    with TestClient(create_app(cfg, autodrain=False)) as c:
        yield c


def test_meta_exposes_tappable_core(client: TestClient) -> None:
    meta = client.get("/api/meta").json()
    ids = {q["id"] for q in meta["core_questions"]}
    assert {"task", "scope", "artifacts"} <= ids
    artifacts_q = next(q for q in meta["core_questions"] if q["id"] == "artifacts")
    assert artifacts_q["kind"] == "multi"
    assert {"version", "llm_name", "routing"} <= meta.keys()


def test_submit_drain_and_read_results(client: TestClient, cfg: Config) -> None:
    body = {
        "raw_request": "Five product ideas from this note",
        "task": "ideas",
        "scope": "import",
        "artifacts": ["hub", "mermaid", "deck"],
        "text": "# Connection\nMeaningful connection predicts health and longevity.\n"
                "Synchrony creates neural coupling between people.",
    }
    created = client.post("/api/jobs", json=body)
    assert created.status_code == 200
    job_id = created.json()["id"]

    # queued and visible
    listed = client.get("/api/jobs").json()
    assert any(j["id"] == job_id and j["status"] == "queued" for j in listed)

    # the Mac worker drains it
    drain_queue(cfg)

    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "done"
    hub = job["result"]["hub_note_path"]
    assert hub and Path(hub).is_file()

    # the produced hub note is fetchable through the artifact endpoint
    art = client.get("/api/jobs/_/artifact", params={"path": hub})
    assert art.status_code == 200
    assert "research-to-artifact" in art.text  # frontmatter tag


def test_artifact_endpoint_blocks_path_traversal(client: TestClient) -> None:
    r = client.get("/api/jobs/_/artifact", params={"path": "/etc/passwd"})
    assert r.status_code == 403


def test_answer_flow_requeues_parked_job(client: TestClient, cfg: Config) -> None:
    queue = FolderJobQueue(cfg.paths.queue())
    job = Job(id="park123", answers=ElicitationAnswers(raw_request="ambiguous ask"))
    q = Question(id="anchor", text="Which concept to anchor on?", kind="single",
                 options=["connection", "synchrony"])
    queue.needs_input(job, [q])

    parked = client.get("/api/jobs/park123").json()
    assert parked["status"] == "needs_input"
    assert parked["followups"][0]["id"] == "anchor"

    answered = client.post("/api/jobs/park123/answers",
                           json={"answers": {"anchor": "synchrony"}})
    assert answered.status_code == 200
    assert client.get("/api/jobs/park123").json()["status"] == "queued"

    # answering a non-parked job is a conflict
    assert client.post("/api/jobs/park123/answers", json={"answers": {}}).status_code == 409
