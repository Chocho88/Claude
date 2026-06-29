"""demo_run — a full pipeline run rendered through the real output code, no API.

Retrieval, citation resolution, the hub-note renderer and the intent timeline
are all the actual engine. The LLM-shaped steps (planning, synthesis, reflection)
are authored here to stand in for the model that would normally fill them — this
is the "Claude acts as the model in chat" path. Swap a real LLMProvider in and
the same StageContext flows through the orchestrator unchanged.

    python scripts/demo_run.py            # write + print the artifact
"""

from __future__ import annotations

import sys
from pathlib import Path

from r2a.config import Config
from r2a.domain.job import Constraints, ElicitationAnswers, Job
from r2a.domain.plan import PlanSpec, Scope, TaskType
from r2a.domain.synthesis import SynthesisOutput, SynthItem
from r2a.domain.trace import RoutingTarget, StageName, TraceRecord
from r2a.factory import default_embedder, default_store
from r2a.output.hub_note import render_hub_note
from r2a.pipeline.stage import StageContext
from r2a.pipeline.tracer import Tracer

LLM = "claude (this chat)"
RAW = "give me product ideas grounded in my interests and values"


def retrieve(embedder, store):
    """Real retrieval: merge a few themed queries into one candidate set."""
    queries = [
        "humane live music sharing with a close inner circle, no vanity metrics",
        "startup strategy positioning know yourself research into artifact",
        "own your files plain text longevity markdown notes",
    ]
    seen: dict[str, object] = {}
    for q in queries:
        for sb in store.search(embedder.embed_query(q), namespace=None, top_k=6):
            seen.setdefault(sb.bite.id, sb)
    return list(seen.values())


def synthesize() -> SynthesisOutput:
    """The deliverable (authored as the model would produce it)."""
    items = [
        SynthItem(
            text="**Crate** — a live, invite-only listening room where an AI weaves "
            "your inner circle's track picks into one continuous future-funk set in "
            "sync: music as a shared present-tense moment, with no follower counts or "
            "vanity metrics.",
            cites=["yf:futurefunk", "cht:persuasive", "op:lens"],
            derived=True,
        ),
        SynthItem(
            text="**Position** — an AI strategy room that ingests your research notes "
            "and keeps a living map of where you're strong and where a market is "
            "underserved, turning 'know yourself / strike where unexpected' into an "
            "inspectable, evidence-linked board.",
            cites=["aow:know", "aow:position", "op:trace"],
            derived=True,
        ),
        SynthItem(
            text="**Over App** — every artifact the tool makes is a plain-Markdown "
            "file you own, with an AI longevity check that flags anything locked to a "
            "proprietary format and rewrites it to open formats.",
            cites=["foa:def", "foa:portable", "op:throughline"],
            derived=True,
        ),
    ]
    mermaid = (
        "graph LR\n"
        '  M["future-funk + anti-engagement"] --> Crate["Crate"]\n'
        '  S["know yourself + positioning"] --> Position["Position"]\n'
        '  F["file over app"] --> Over["Over App"]'
    )
    return SynthesisOutput(
        title="Profile-grounded product ideas",
        summary="Three AI-native concepts derived from the operator's own corpus "
        "(music taste, strategy frame, humane-tech values, file-over-app). Each is "
        "flagged _derived_ — the sources describe the principles; they do not propose "
        "these products. Scope = just the import.",
        items=items,
        mermaid=mermaid,
        score=91,
    )


def build_trace(retrieved) -> Tracer:
    t = Tracer()
    rec = lambda **k: TraceRecord(llm_used=LLM, attempt=0, **k)  # noqa: E731
    t.add(rec(
        stage=StageName.ELICITATION, confidence=0.88,
        intent_understanding="Produce product ideas grounded in the operator's "
        "interests/values corpus; scope = just the import.",
        inputs_used={"raw_request": RAW},
    ))
    t.add(rec(
        stage=StageName.PLANNING, confidence=0.86,
        intent_understanding="task = ideas; derive one concept per anchored theme "
        "(music/anti-engagement, strategy, file-over-app); shape = Name — what it is; "
        "why it helps; flag everything derived.",
        outputs={"task": "ideas", "scope": "import"},
    ))
    t.add(rec(
        stage=StageName.RETRIEVAL, confidence=0.90,
        intent_understanding="Pull the bites relevant to each theme from the profile "
        "store; admit no model/web knowledge (scope = import).",
        inputs_used={"namespaces": sorted({sb.bite.namespace for sb in retrieved})},
        outputs={"retrieved": [sb.bite.id for sb in retrieved]},
    ))
    t.add(rec(
        stage=StageName.SYNTHESIS, confidence=0.87,
        intent_understanding="3 cited, derived-flagged ideas in the planned shape; "
        "apply the ideation lens (AI-native, contextual trust, live, collaborative, "
        "anti-exploitation).",
    ))
    t.add(rec(
        stage=StageName.REFLECTION, confidence=0.91,
        intent_understanding="Grade grounding, citations and lens-fit; all hold → ship.",
        outputs={"routing_target": RoutingTarget.SHIP.value, "score": 91,
                 "issue_type": "NONE"},
    ))
    return t


def main() -> None:
    config = Config.load()
    embedder = default_embedder(config)
    store = default_store(config)
    if not store.namespaces():
        sys.exit("store is empty — run: python scripts/seed_profile.py")

    retrieved = retrieve(embedder, store)
    draft = synthesize()
    tracer = build_trace(retrieved)

    ctx = StageContext(
        job=Job(id="profile-ideas"),
        answers=ElicitationAnswers(
            raw_request=RAW, scope=Scope.IMPORT, task=TaskType.IDEAS,
            constraints=Constraints(count=3, audience="the operator"),
        ),
        plan=PlanSpec(
            intent="product ideas grounded in the operator's corpus",
            scope=Scope.IMPORT, task=TaskType.IDEAS,
            strategy="one concept per anchored theme, strictly cited",
            answer_shape="Name — what it is; why it helps",
        ),
        retrieved=retrieved,
        draft=draft,
    )

    note = render_hub_note(ctx, tracer)

    out_dir = config.paths.vault() / "profile-ideas"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "Profile-grounded product ideas.md").write_text(note)
    (out_dir / "trace.json").write_text(tracer.to_json())

    print(note)
    print(f"\n--- written to {out_dir} ---")


if __name__ == "__main__":
    main()
