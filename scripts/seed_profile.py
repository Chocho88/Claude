"""Bootstrap the operator-profile vector DB from data/profile_seed.json (M6).

Real path, no API needed: it uses the same Embedder + VectorStore the pipeline
uses (factory.default_embedder / default_store), so the bites land in the actual
store the Retrieval stage queries. The LLM is not involved — these bites were
extracted from cited web sources (and the user's context reference) up front.

    python scripts/seed_profile.py            # load into the configured store
    python scripts/seed_profile.py --reset    # drop the seed namespaces first
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from r2a.config import Config
from r2a.domain.bite import BiteType, KnowledgeBite
from r2a.factory import default_embedder, default_store

SEED = Path(__file__).resolve().parent.parent / "data" / "profile_seed.json"


def load_bites() -> list[KnowledgeBite]:
    raw = json.loads(SEED.read_text())["bites"]
    return [
        KnowledgeBite(
            id=b["id"],
            text=b["text"],
            type=BiteType(b["type"]),
            source_title=b["source_title"],
            author=b.get("author"),
            location=b.get("location"),
            namespace=b["namespace"],
        )
        for b in raw
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed the profile vector DB.")
    ap.add_argument("--reset", action="store_true", help="drop seed namespaces first")
    ap.add_argument("--config", default=None, help="path to a TOML config")
    args = ap.parse_args()

    config = Config.load(args.config)
    embedder = default_embedder(config)
    store = default_store(config)

    bites = load_bites()
    # Embed each bite's text and attach the vector (the real ingest path).
    vecs = embedder.embed([b.text for b in bites])
    for b, v in zip(bites, vecs):
        b.embedding = v

    if args.reset:
        for ns in sorted({b.namespace for b in bites}):
            store.delete_namespace(ns)

    store.upsert(bites)

    by_ns = Counter(b.namespace for b in bites)
    print(f"store:     {config.paths.store()}")
    print(f"embedder:  {embedder.model_id} (dim {embedder.dim})")
    print(f"seeded {len(bites)} bites across {len(by_ns)} namespaces:")
    for ns, n in sorted(by_ns.items()):
        print(f"  - {ns:18s} {n} bites")
    print(f"namespaces now in store: {store.namespaces()}")


if __name__ == "__main__":
    main()
