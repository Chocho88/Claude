"""JobQueue ABC. The folder-based implementation (M4) is the local stand-in for
the iCloud-synced queue; the Mac is the single writer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from r2a.domain.job import Job, JobResult


class JobQueue(ABC):
    @abstractmethod
    def enqueue(self, job: Job) -> None:
        ...

    @abstractmethod
    def claim_next(self) -> Job | None:
        """Atomically claim the next queued job, marking it RUNNING."""

    @abstractmethod
    def complete(self, job: Job, result: JobResult) -> None:
        ...

    @abstractmethod
    def fail(self, job: Job, error: str) -> None:
        ...
