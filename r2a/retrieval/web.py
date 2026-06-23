"""Web search behind an interface — disabled unless scope explicitly allows it.

Privacy: a query reaches this provider only when the job's scope is IMPORT_WEB,
which is the moment content may leave the device. The default provider is a
no-op so the offline pipeline never reaches the network by accident.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class WebResult(BaseModel):
    title: str
    url: str
    snippet: str


class WebSearchProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def search(self, query: str, *, max_results: int = 5) -> list[WebResult]:
        ...


class DisabledWebSearch(WebSearchProvider):
    """Returns nothing; the safe default when web scope isn't granted."""

    name = "disabled"

    def search(self, query: str, *, max_results: int = 5) -> list[WebResult]:
        return []
