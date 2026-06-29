"""M3: deck + HTML prototype are produced and linked from the hub note."""

from __future__ import annotations

from pathlib import Path

from r2a.adapters.llm.stub import StubProvider
from r2a.config import Config
from r2a.domain.artifact import ArtifactType
from r2a.domain.job import Constraints
from r2a.domain.plan import TaskType
from r2a.pipeline.orchestrator import run_pipeline
from r2a.pipeline.stage import Deps
from r2a.pipeline.tracer import Tracer

from tests.conftest import make_answers, make_ctx


def _run(tmp_path, store, embedder, artifacts):
    answers = make_answers(task=TaskType.IDEAS)
    answers.constraints = Constraints(count=3, artifacts=artifacts)
    ctx = make_ctx(answers)
    deps = Deps(llm=StubProvider(), embedder=embedder, store=store,
                tracer=Tracer(), config=Config())
    return run_pipeline(ctx, deps, out_dir=tmp_path), ctx


def test_deck_and_html_are_written_and_linked(tmp_path, store, embedder):
    res, _ = _run(
        tmp_path, store, embedder,
        [ArtifactType.HUB, ArtifactType.MERMAID, ArtifactType.DECK, ArtifactType.HTML],
    )

    paths = {Path(p).name for p in res.result.artifact_paths}
    deck = next(p for p in res.result.artifact_paths if p.endswith("-deck.md"))
    html = next(p for p in res.result.artifact_paths if p.endswith("-prototype.html"))

    deck_text = Path(deck).read_text()
    assert "\n---\n" in deck_text  # Obsidian Slides separators
    assert deck_text.startswith("---")  # frontmatter
    assert "## Source" in deck_text

    html_text = Path(html).read_text()
    assert html_text.lstrip().startswith("<!doctype html")
    assert "Research to Artifact" in html_text
    assert "const ITEMS" in html_text  # self-contained data, no external deps

    hub_text = Path(res.result.hub_note_path).read_text()
    assert "## Artifacts" in hub_text
    assert "[[" in hub_text and "-deck]]" in hub_text  # deck wikilink
    assert "-prototype.html)" in hub_text  # html link


def test_no_artifacts_requested_writes_only_hub(tmp_path, store, embedder):
    res, _ = _run(tmp_path, store, embedder, [ArtifactType.HUB])
    names = [Path(p).name for p in res.result.artifact_paths]
    assert all(not n.endswith("-deck.md") and not n.endswith(".html") for n in names)
    assert "## Artifacts" not in Path(res.result.hub_note_path).read_text()
