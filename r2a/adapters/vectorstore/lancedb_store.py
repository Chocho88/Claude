"""LanceDBStore — file-based vector store (M1). Single-writer (the Mac/worker).

Namespace is a filter column so retrieval scopes to one import and the swap to
sqlite-vec stays mechanical. Cosine distance over normalized embeddings; the
returned score is 1 - distance.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from r2a.domain.bite import BiteType, KnowledgeBite, ScoredBite
from r2a.domain.common import Vector, utcnow

from .base import VectorStore

_TABLE = "bites"


def _row(bite: KnowledgeBite) -> dict:
    return {
        "id": bite.id,
        "text": bite.text,
        "type": bite.type.value,
        "source_title": bite.source_title,
        "author": bite.author or "",
        "location": bite.location or "",
        "namespace": bite.namespace,
        "confidence": bite.confidence,
        "created_at": bite.created_at.isoformat(),
        "vector": bite.embedding,
    }


def _bite(row: dict) -> KnowledgeBite:
    try:
        created = datetime.fromisoformat(row["created_at"])
    except (KeyError, ValueError):
        created = utcnow()
    return KnowledgeBite(
        id=row["id"],
        text=row["text"],
        type=BiteType(row["type"]),
        source_title=row["source_title"],
        author=row.get("author") or None,
        location=row.get("location") or None,
        namespace=row["namespace"],
        embedding=list(row["vector"]) if row.get("vector") is not None else None,
        confidence=row.get("confidence", 1.0),
        created_at=created,
    )


def _quote_in(ids: list[str]) -> str:
    return ", ".join("'" + i.replace("'", "''") + "'" for i in ids)


class LanceDBStore(VectorStore):
    def __init__(self, path: str | Path) -> None:
        try:
            import lancedb
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "Vector store needs the 'vector' extra: pip install -e '.[vector]'"
            ) from e
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(self.path))

    def _open(self):
        # table_names() returns a plain list; list_tables() returns a paginated
        # object in lancedb 0.33, so we keep the (deprecated but correct) call.
        if _TABLE not in self._db.table_names():
            return None
        return self._db.open_table(_TABLE)

    def upsert(self, bites: list[KnowledgeBite]) -> None:
        if not bites:
            return
        rows = [_row(b) for b in bites]
        tbl = self._open()
        if tbl is None:
            self._db.create_table(_TABLE, data=rows)
            return
        tbl.delete(f"id IN ({_quote_in([b.id for b in bites])})")
        tbl.add(rows)

    def search(
        self,
        query_vec: Vector,
        *,
        namespace: str | None,
        top_k: int,
        filters: dict | None = None,
    ) -> list[ScoredBite]:
        tbl = self._open()
        if tbl is None:
            return []
        q = tbl.search(query_vec).metric("cosine").limit(top_k)
        if namespace is not None:
            q = q.where(f"namespace = '{namespace}'", prefilter=True)
        out: list[ScoredBite] = []
        for row in q.to_list():
            distance = row.get("_distance", 0.0)
            out.append(ScoredBite(bite=_bite(row), score=round(1.0 - distance, 4)))
        return out

    def delete_namespace(self, namespace: str) -> None:
        tbl = self._open()
        if tbl is not None:
            tbl.delete(f"namespace = '{namespace}'")

    def namespaces(self) -> list[str]:
        tbl = self._open()
        if tbl is None:
            return []
        return sorted(set(tbl.to_arrow().column("namespace").to_pylist()))
