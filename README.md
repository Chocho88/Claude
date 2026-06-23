# Research to Artifact

A **local-first agentic app** that turns imported content (research papers, articles, ideas,
raw text, uploaded files) into a **grounded, multimodal Obsidian artifact**, using an
**instrumented linear multi-agent pipeline** backed by a **local vector database of "knowledge
bites."**

The non-negotiable virtue is **fidelity + traceability**: every output item traces to a source
bite; ideas beyond the source are flagged as derived; the user controls how far past the source
the system may reach; and when the system misreads intent, the trace pinpoints **which agent
stage** diverged.

## Status

Built incrementally (see `r2a/` and the milestones below). The current target is a
**Claude-API-first vertical slice** that runs and is testable on Linux today, with local
components (Gemma, iCloud sync, the PWA client) swappable in behind adapter interfaces on a Mac.

| Milestone | Scope | Testable here |
|-----------|-------|---------------|
| M0 | Skeleton, domain models, adapter ABCs, stub providers, pipeline + loop, tracer | ✅ done |
| M1 | Real ingest (pdf/docx/md/txt), sentence-transformers embeddings, LanceDB | ✅ done |
| M2 | Claude provider (forced tool-use JSON), real end-to-end run | ✅ done (live needs `ANTHROPIC_API_KEY`) |
| M3 | Output artifacts: hub note, mermaid, HTML prototype, Obsidian-Slides deck | ✅ done |
| M4 | Folder job queue + `r2a ingest/enqueue/worker/run` CLI | ✅ done |
| M5+ | Local Gemma (Ollama/MLX), iCloud sync, PWA client, sqlite-vec | on a Mac |

## Usage

```bash
python -m pip install -e ".[slice,dev]"   # full slice (torch/lancedb/anthropic)

# One-shot: ingest a document, run the pipeline, write artifacts to the vault
r2a run paper.pdf --task ideas --artifacts hub,mermaid,deck,html --config config.toml

# Or the queue flow (what the iPhone client drives): drop a job, drain it on the Mac
r2a enqueue paper.pdf --task ideas --config config.toml
r2a worker --config config.toml
```

Without `ANTHROPIC_API_KEY` or local-model deps the engine still runs end-to-end on
the offline stubs (deterministic), so the queue/output plumbing is fully testable.

## Architecture (one-paragraph)

`domain/` (pure pydantic models) and `pipeline/` (stages + orchestrator) depend **only** on
adapter **ABCs** in `adapters/*/base.py` — never on a concrete implementation. Concretes
(`ClaudeProvider`, `SentenceTransformerEmbedder`, `LanceDBStore`, and their stub doubles) are
wired at the edges by `r2a/factory.py`. An `import-linter` contract enforces this so the
Claude→Gemma and LanceDB→sqlite-vec swaps stay cheap. The pipeline runs
`Elicitation → Planning → Retrieval → (Synthesis → Reflection)* → Output`; every stage emits a
`TraceRecord` with its own `intent_understanding`, and Reflection's `routing_target` names the
stage it blames — so the trace localizes where intent diverged.

## Install & test

```bash
python -m pip install -e ".[dev]"     # M0: light, no heavy ML deps
pytest                                # offline suite (stubs); excludes -m live

# Later milestones:
python -m pip install -e ".[slice,dev]"   # pulls torch/lancedb/anthropic
pytest -m live                            # opt-in: hits Claude + real models
lint-imports                              # verify the dependency contract
```

## Privacy

Content never leaves the device unless **Claude fallback** or **web scope** is explicitly
invoked. The active routing mode (`auto | force_local | force_claude`) and any off-device call
are surfaced in the UI and recorded in every `TraceRecord`'s `llm_used` field.

## Legacy

The repo previously held an unrelated "Israel Siren Statistics" React app; it is preserved
under `legacy/siren-stats/`.
