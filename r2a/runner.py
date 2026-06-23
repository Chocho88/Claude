"""Tie ingest + pipeline into one job run, and drain the queue.

Edge module (may import concretes/factory). The worker builds the heavy adapters
(LLM, embedder, store) once and gives each job a fresh Tracer.
"""

from __future__ import annotations

from pathlib import Path

from r2a.config import Config
from r2a.factory import default_embedder, default_llm, default_store
from r2a.ingest import ingest_document
from r2a.pipeline.orchestrator import PipelineResult, run_pipeline
from r2a.pipeline.stage import Deps, StageContext
from r2a.pipeline.tracer import Tracer
from r2a.queue.folder_queue import FolderJobQueue
from r2a.retrieval.web import DisabledWebSearch
from r2a.domain.job import Job


def process_job(job: Job, deps: Deps, config: Config) -> PipelineResult:
    """Ingest any source documents, then run the pipeline into the vault."""
    for path in list(job.source_paths):
        res = ingest_document(
            path, embedder=deps.embedder, store=deps.store, llm=deps.llm
        )
        if res.namespace not in job.namespaces:
            job.namespaces.append(res.namespace)

    ctx = StageContext(job=job, answers=job.answers)
    out_dir = config.paths.vault() / (job.output_dir or job.id)
    return run_pipeline(ctx, deps, out_dir=out_dir)


def drain_queue(config: Config, *, max_jobs: int | None = None) -> list[tuple[str, str]]:
    """Claim and process queued jobs until empty. Returns (job_id, status) pairs.

    Heavy adapters are built once; each job gets a fresh Tracer.
    """
    queue = FolderJobQueue(config.paths.queue())
    llm = default_llm(config)
    embedder = default_embedder(config)
    store = default_store(config)

    done: list[tuple[str, str]] = []
    while max_jobs is None or len(done) < max_jobs:
        job = queue.claim_next()
        if job is None:
            break
        deps = Deps(
            llm=llm, embedder=embedder, store=store,
            tracer=Tracer(), config=config, web=DisabledWebSearch(),
        )
        try:
            result = process_job(job, deps, config)
        except Exception as e:  # keep the worker alive across one bad job
            queue.fail(job, repr(e))
            done.append((job.id, "failed"))
            continue
        if result.status.value == "needs_input":
            queue.needs_input(job, result.followups)
            done.append((job.id, "needs_input"))
        else:
            queue.complete(job, result.result)
            done.append((job.id, "done"))
    return done


def vault_path_for(config: Config, job_id: str) -> Path:
    return config.paths.vault() / job_id
