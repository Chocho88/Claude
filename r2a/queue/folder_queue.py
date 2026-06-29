"""FolderJobQueue — a folder of job files; the local stand-in for the iCloud queue.

State directories: queued/ running/ done/ failed/ needs_input/. `claim_next`
uses an atomic os.rename from queued/ to running/ as the single-writer lock, so a
crash mid-job leaves the file in running/ (recoverable) rather than lost. The
iPhone only drops files into queued/ and reads done/; the Mac is the only writer
of the store and the only worker draining the queue.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from r2a.domain.job import Job, JobResult, JobStatus

_STATES = ("queued", "running", "done", "failed", "needs_input")


class FolderJobQueue:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        for state in _STATES:
            (self.root / state).mkdir(parents=True, exist_ok=True)

    def _dir(self, state: str) -> Path:
        return self.root / state

    def _write(self, state: str, job: Job) -> Path:
        path = self._dir(state) / f"{job.id}.json"
        path.write_text(job.model_dump_json(indent=2), encoding="utf-8")
        return path

    def enqueue(self, job: Job) -> None:
        job.status = JobStatus.QUEUED
        self._write("queued", job)

    def claim_next(self) -> Job | None:
        """Atomically claim the oldest queued job, moving it to running/."""
        for src in sorted(self._dir("queued").glob("*.json")):
            dst = self._dir("running") / src.name
            try:
                os.rename(src, dst)  # atomic within the same filesystem
            except (FileNotFoundError, OSError):
                continue  # another worker claimed it; try the next
            job = Job.model_validate_json(dst.read_text(encoding="utf-8"))
            job.status = JobStatus.RUNNING
            job.touch()
            self._write("running", job)
            return job
        return None

    def _clear_running(self, job: Job) -> None:
        (self._dir("running") / f"{job.id}.json").unlink(missing_ok=True)

    def complete(self, job: Job, result: JobResult) -> None:
        job.status = JobStatus.DONE
        job.result = result
        job.touch()
        self._write("done", job)
        self._clear_running(job)

    def fail(self, job: Job, error: str) -> None:
        job.status = JobStatus.FAILED
        job.result = JobResult(error=error)
        job.touch()
        self._write("failed", job)
        self._clear_running(job)

    def needs_input(self, job: Job, followups) -> None:
        """Park a job awaiting follow-up answers (Planning asked for more)."""
        job.status = JobStatus.NEEDS_INPUT
        job.touch()
        path = self._dir("needs_input") / f"{job.id}.json"
        payload = job.model_dump(mode="json")
        payload["followups"] = [q.model_dump(mode="json") for q in (followups or [])]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._clear_running(job)

    # --- read side (used by the server for status/results) -----------------

    def read(self, job_id: str) -> tuple[str, dict] | None:
        """Find a job by id across all states; return (state, raw_payload)."""
        for state in _STATES:
            path = self._dir(state) / f"{job_id}.json"
            if path.exists():
                return state, json.loads(path.read_text(encoding="utf-8"))
        return None

    def list_jobs(self) -> list[tuple[str, dict]]:
        """All jobs across states, newest first by file mtime."""
        found: list[tuple[float, str, dict]] = []
        for state in _STATES:
            for path in self._dir(state).glob("*.json"):
                payload = json.loads(path.read_text(encoding="utf-8"))
                found.append((path.stat().st_mtime, state, payload))
        found.sort(key=lambda t: t[0], reverse=True)
        return [(state, payload) for _, state, payload in found]

    def submit_answers(self, job_id: str, answers: dict[str, str]) -> Job | None:
        """Merge follow-up answers into a parked job and re-queue it.

        Returns the re-queued Job, or None if the job isn't awaiting input.
        """
        rec = self.read(job_id)
        if rec is None or rec[0] != "needs_input":
            return None
        job = Job.model_validate(rec[1])  # extra "followups" key is ignored
        job.answers.followups.update(answers)
        (self._dir("needs_input") / f"{job_id}.json").unlink(missing_ok=True)
        self.enqueue(job)
        return job
