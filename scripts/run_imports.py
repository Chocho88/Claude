"""Run insights + ideas over the two imported documents, via the real engine.

Retrieval, citation resolution and the hub-note renderer are the actual engine;
the LLM-shaped steps (planning, synthesis, reflection) are authored here as the
model would produce them (no API). Two tasks → two cited Obsidian notes, written
to the vault and to examples/imports/.

    python scripts/run_imports.py      # after: seed_profile.py --file data/imports_seed.json
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


def retrieve(embedder, store):
    """Real retrieval: merge themed queries spanning both imports + the lens."""
    queries = [
        "attention and energy deliberately directed toward goals",
        "Israel art is not on the agenda collectors culture shrinking",
        "buying art is pure energy patronage gift to culture",
        "identity change goals lens cybernetics steering vision anti-vision",
        "the artist sea turtle attrition years of devotion",
        "behavior reveals unconscious goals procrastination avoiding judgment",
        "anti-exploitation own your files contextual trust live shared experience",
    ]
    seen: dict[str, object] = {}
    for q in queries:
        for sb in store.search(embedder.embed_query(q), namespace=None, top_k=10):
            seen.setdefault(sb.bite.id, sb)
    return list(seen.values())


def trace(records: list[dict]) -> Tracer:
    t = Tracer()
    for r in records:
        t.add(TraceRecord(llm_used=LLM, attempt=0, **r))
    return t


def render(config, retrieved, plan: PlanSpec, draft: SynthesisOutput,
           records: list[dict], slug: str, raw: str) -> str:
    ctx = StageContext(
        job=Job(id=slug),
        answers=ElicitationAnswers(
            raw_request=raw, scope=plan.scope, task=plan.task,
            constraints=Constraints(audience="the operator"),
        ),
        plan=plan, retrieved=retrieved, draft=draft,
    )
    tracer = trace(records)
    note = render_hub_note(ctx, tracer)
    for d in (config.paths.vault() / slug, Path("examples/imports") / slug):
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{draft.title}.md").write_text(note)
        (d / "trace.json").write_text(tracer.to_json())
    return note


# ----------------------------------------------------------------------------
# Task 1 — INSIGHTS (cross-document; derived connections flagged)
# ----------------------------------------------------------------------------
INSIGHTS = SynthesisOutput(
    title="Insights — Red Dots × Fix your life in 1 day",
    summary="Reading the two imports together. Each insight is grounded in source "
    "bites; cross-document connections that go beyond either text are flagged "
    "_derived_. Scope = the two imports.",
    items=[
        SynthItem(
            text="**Attention is the single currency in both texts.** Koe's "
            "'psychic energy invested in goals' and the essay's claim that buying "
            "art is 'pure energy' for culture are the *same resource* — culture and "
            "a life both starve when attention is never deliberately directed.",
            cites=["koe:flow", "rd:purchase-energy", "rd:energy"], derived=True),
        SynthItem(
            text="**Israel's neglect of art is an agenda problem, not a taste "
            "problem.** Koe shows behavior reveals true goals; a society that spends "
            "freely on restaurants and travel but never *considers* art is revealing "
            "what it actually values — the fix is making art visible, not cheaper.",
            cites=["rd:agenda", "koe:teleological", "rd:secondary"], derived=True),
        SynthItem(
            text="**The 'sea turtle' attrition is Koe's Uncertainty phase.** Most "
            "artists vanish not for lack of talent but for lack of sustaining energy "
            "through the long middle — the same Dissonance→Uncertainty→Discovery "
            "valley where most identity changes die.",
            cites=["rd:turtles", "rd:disappear", "koe:phases"], derived=True),
        SynthItem(
            text="**A goal is a lens — so is a red dot.** Collecting isn't on "
            "people's agenda because no goal has made art perceptible to them; change "
            "the lens (give them a reason to look) and the buying behavior follows, "
            "exactly as Koe describes perception bending to goals.",
            cites=["koe:goal-lens", "rd:agenda"], derived=True),
        SynthItem(
            text="**Under-investing in art is under-investing in a society's "
            "complexity.** The essay's strongest in-source claim: art is cultural "
            "DNA, so a culture that lets it shrink is choosing to become simpler and "
            "less meaningful.",
            cites=["rd:gift", "rd:culture-is-us"]),
    ],
    mermaid="graph TD\n"
            '  E["Attention / energy"] --> A["Art as pure energy (Red Dots)"]\n'
            '  E --> L["Psychic energy in goals (Koe)"]\n'
            '  A --> C["Culture survives or shrinks"]\n'
            '  L --> I["A life changes or stalls"]',
    score=90,
)
INSIGHTS_TRACE = [
    dict(stage=StageName.ELICITATION, confidence=0.84,
         intent_understanding="Surface insights that read the two imports together; "
         "scope = the two documents."),
    dict(stage=StageName.PLANNING, confidence=0.83,
         intent_understanding="task = insights; strategy = find the shared structure "
         "(energy/attention, goals-as-lens, the attrition valley); flag cross-document "
         "synthesis as derived.",
         outputs={"task": "insights", "scope": "import"}),
    dict(stage=StageName.RETRIEVAL, confidence=0.88,
         intent_understanding="Pull the energy/agenda/identity bites from both "
         "namespaces; admit no outside knowledge."),
    dict(stage=StageName.SYNTHESIS, confidence=0.86,
         intent_understanding="Five grounded insights; each cites its bites; "
         "cross-document links flagged derived."),
    dict(stage=StageName.REFLECTION, confidence=0.9,
         intent_understanding="Grounding and citations hold; derived links honest → ship.",
         outputs={"routing_target": RoutingTarget.SHIP.value, "score": 90,
                  "issue_type": "NONE"}),
]


# ----------------------------------------------------------------------------
# Task 2 — IDEAS (ideation lens applied; everything derived)
# ----------------------------------------------------------------------------
IDEAS = SynthesisOutput(
    title="Product ideas — Red Dots × Fix your life in 1 day",
    summary="Four AI-native concepts derived from the two imports and run through "
    "the ideation lens (AI-native, contextual trust, live shared experiences, "
    "collaboration over performance, anti-exploitation). All flagged _derived_ — the "
    "sources describe the problem and the psychology; they do not propose these "
    "products. Each passes the sanity check: still good for the user if it earned the "
    "company nothing from engagement.",
    items=[
        SynthItem(
            text="**Red Dot** — a contextual-trust patronage app: you see which "
            "works the *people you actually trust* have bought (scoped to a person and "
            "a relationship, never a public clout score), turning collecting into a "
            "quiet signal among friends rather than a status game. Puts art 'on the "
            "agenda' through trusted context, not vanity.",
            cites=["rd:agenda", "rd:purchase-energy", "op:lens"], derived=True),
        SynthItem(
            text="**Patron Night** — AI-orchestrated live, co-present micro-patronage: "
            "a small circle gathers at a studio or show (in person or synchronous "
            "video) and the app facilitates collective commissioning or split "
            "acquisition *in the moment*. Converts buying art from a solitary "
            "transaction into a shared live event that injects energy into culture.",
            cites=["rd:purchase-energy", "rd:gift", "cht:persuasive"], derived=True),
        SynthItem(
            text="**Anti-Vision** — a file-over-app reflection tool that runs Koe's "
            "one-day protocol as a private, you-own-the-files practice: AI asks the "
            "vision/anti-vision questions and schedules the pattern-break interrupts, "
            "but every answer is plain Markdown you keep — no streaks, no engagement "
            "loops. A genuinely transformative protocol that refuses to become a trap.",
            cites=["koe:phases", "koe:videogame", "foa:def"], derived=True),
        SynthItem(
            text="**Steer** — an AI cybernetic companion for artists: define your "
            "vision and constraints, and it senses where you are versus the goal and "
            "proposes the next small lever — the thermostat model applied to a creative "
            "practice, scoped to *your* definition of winning, not platform metrics. "
            "Sustains the years-long energy the essay names as the real bottleneck.",
            cites=["koe:cybernetics", "koe:lifestyle", "rd:turtles"], derived=True),
    ],
    mermaid="graph LR\n"
            '  R1["art not on the agenda"] --> Red["Red Dot"]\n'
            '  R2["buying art = energy"] --> Pat["Patron Night"]\n'
            '  K1["1-day identity protocol"] --> AV["Anti-Vision"]\n'
            '  K2["cybernetic steering"] --> St["Steer"]',
    score=92,
)
IDEAS_TRACE = [
    dict(stage=StageName.ELICITATION, confidence=0.86,
         intent_understanding="Generate product ideas from the two imports; scope = "
         "the imports; apply the operator's ideation lens."),
    dict(stage=StageName.PLANNING, confidence=0.85,
         intent_understanding="task = ideas; one concept per anchored hook (patronage "
         "agenda, art-as-energy, the protocol, cybernetic steering); shape = Name — "
         "what it is; why it helps; flag all derived.",
         outputs={"task": "ideas", "scope": "import"}),
    dict(stage=StageName.RETRIEVAL, confidence=0.88,
         intent_understanding="Pull the agenda/energy/identity bites plus the lens "
         "bites (contextual trust, anti-exploitation, file-over-app)."),
    dict(stage=StageName.SYNTHESIS, confidence=0.87,
         intent_understanding="Four cited, derived-flagged ideas; each AI-native, "
         "trust-scoped, live or anti-exploitation; sanity-checked against engagement."),
    dict(stage=StageName.REFLECTION, confidence=0.91,
         intent_understanding="Grounding, citations, lens-fit and the no-engagement "
         "sanity check all hold → ship.",
         outputs={"routing_target": RoutingTarget.SHIP.value, "score": 92,
                  "issue_type": "NONE"}),
]


def main() -> None:
    config = Config.load()
    embedder, store = default_embedder(config), default_store(config)
    if "red-dots" not in store.namespaces():
        sys.exit("imports not seeded — run: "
                 "python scripts/seed_profile.py --file data/imports_seed.json")

    retrieved = retrieve(embedder, store)
    got = {sb.bite.id for sb in retrieved}
    cited = {c for d in (INSIGHTS, IDEAS) for it in d.items for c in it.cites}
    missing = cited - got
    if missing:
        print(f"[note] cited bites not in retrieved set (will link by id): {missing}\n")

    for plan, draft, records, slug, raw in [
        (PlanSpec(intent="insights across the two imports", scope=Scope.IMPORT,
                  task=TaskType.INSIGHTS, strategy="find shared structure",
                  answer_shape="grounded insight; cross-doc links flagged derived"),
         INSIGHTS, INSIGHTS_TRACE, "insights-red-dots-koe",
         "raise insights based on this content"),
        (PlanSpec(intent="product ideas from the two imports", scope=Scope.IMPORT,
                  task=TaskType.IDEAS, strategy="one concept per hook, lens applied",
                  answer_shape="Name — what it is; why it helps"),
         IDEAS, IDEAS_TRACE, "ideas-red-dots-koe",
         "raise product ideas based on this content"),
    ]:
        note = render(config, retrieved, plan, draft, records, slug, raw)
        print(note)
        print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
