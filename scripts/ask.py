"""ask — real retrieval against the populated vector DB (the prototype's core).

No API key, no model download: it embeds your query with the configured Embedder
and runs an actual vector search over the bites seeded by seed_profile.py. This is
the genuine Retrieval stage, usable from the terminal (or driven through chat).

    python scripts/ask.py "humane way to share music with close friends"
    python scripts/ask.py "startup positioning" --namespace art-of-war --k 5
"""

from __future__ import annotations

import argparse

from r2a.config import Config
from r2a.factory import default_embedder, default_store


def main() -> None:
    ap = argparse.ArgumentParser(description="Query the profile vector DB.")
    ap.add_argument("query", help="what to retrieve")
    ap.add_argument("--namespace", default=None, help="scope to one source (default: all)")
    ap.add_argument("--k", type=int, default=6, help="how many bites to return")
    ap.add_argument("--config", default=None, help="path to a TOML config")
    args = ap.parse_args()

    config = Config.load(args.config)
    embedder = default_embedder(config)
    store = default_store(config)

    if not store.namespaces():
        raise SystemExit("store is empty — run: python scripts/seed_profile.py")

    qv = embedder.embed_query(args.query)
    hits = store.search(qv, namespace=args.namespace, top_k=args.k)

    scope = args.namespace or "all namespaces"
    print(f'query:  "{args.query}"   (scope: {scope}, embedder: {embedder.model_id})\n')
    for i, sb in enumerate(hits, 1):
        b = sb.bite
        cite = f"({b.author}, {b.source_title})" if b.author else f"({b.source_title})"
        print(f"{i}. [{sb.score:+.3f}] [{b.type.value}] {b.id}  ·  {b.namespace}")
        print(f"   {b.text}")
        print(f"   ↳ {cite}  {b.location or ''}\n")


if __name__ == "__main__":
    main()
