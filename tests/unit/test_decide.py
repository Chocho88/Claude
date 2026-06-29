"""Exhaustive routing + a termination property test for the pure decide()."""

from __future__ import annotations

import itertools

from r2a.domain.reflection import ReflectionResult
from r2a.domain.trace import IssueType, RoutingTarget
from r2a.pipeline.decide import Decision, decide
from r2a.pipeline.stage import RunCounters


def R(routing: RoutingTarget, issue: IssueType = IssueType.NONE) -> ReflectionResult:
    return ReflectionResult(routing_target=routing, issue_type=issue, score=50)


def test_ship_short_circuits_regardless_of_counters():
    for synth, esc in itertools.product(range(5), range(3)):
        c = RunCounters(synth_attempts=synth, escalations_used=esc)
        assert decide(R(RoutingTarget.SHIP), c) == Decision.SHIP


def test_resynth_while_budget_remains():
    for synth in range(3):  # 0,1,2 < 3
        c = RunCounters(synth_attempts=synth)
        assert decide(R(RoutingTarget.SYNTHESIS), c) == Decision.RESYNTH


def test_escalation_targets_by_issue_when_synth_budget_spent():
    c = RunCounters(synth_attempts=3, escalations_used=0)
    assert decide(R(RoutingTarget.RETRIEVAL, IssueType.EVIDENCE_GAP), c) == (
        Decision.ESCALATE_RETRIEVAL
    )
    assert decide(R(RoutingTarget.PLANNING, IssueType.INTENT_OR_STRATEGY), c) == (
        Decision.ESCALATE_PLANNING
    )


def test_format_issue_with_no_budget_ships_best():
    c = RunCounters(synth_attempts=3, escalations_used=0)
    assert decide(R(RoutingTarget.SYNTHESIS, IssueType.FORMAT), c) == Decision.SHIP_BEST


def test_ships_best_once_escalation_spent():
    c = RunCounters(synth_attempts=3, escalations_used=1)
    assert decide(R(RoutingTarget.PLANNING, IssueType.INTENT_OR_STRATEGY), c) == (
        Decision.SHIP_BEST
    )


def _simulate(reflections, *, max_synth=3, max_esc=1, hard_cap=1000) -> int:
    """Drive the same counter transitions the orchestrator uses; return #steps."""
    c = RunCounters()
    steps = 0
    refl_iter = iter(reflections)
    while True:
        steps += 1
        assert steps < hard_cap, "decide() failed to terminate"
        try:
            r = next(refl_iter)
        except StopIteration:
            # Worst case: keep failing forever; must still terminate.
            r = R(RoutingTarget.SYNTHESIS, IssueType.INTENT_OR_STRATEGY)
        c.synth_attempts += 1
        d = decide(r, c, max_synth_per_phase=max_synth, max_escalations=max_esc)
        if d in (Decision.SHIP, Decision.SHIP_BEST):
            return steps
        if d == Decision.RESYNTH:
            continue
        # escalation: fresh phase
        c.escalations_used += 1
        c.synth_attempts = 0


def test_termination_under_adversarial_failures():
    # Always-fail with the worst escalating issue must still terminate, and within
    # the analytic bound: max_synth (phase 1) + max_synth (phase 2 after escalation).
    steps = _simulate([], max_synth=3, max_esc=1)
    assert steps <= 3 + 3


def test_termination_for_all_short_sequences():
    routings = [RoutingTarget.SHIP, RoutingTarget.SYNTHESIS, RoutingTarget.PLANNING]
    issues = [IssueType.NONE, IssueType.EVIDENCE_GAP, IssueType.INTENT_OR_STRATEGY]
    pool = [R(rt, iss) for rt in routings for iss in issues]
    for combo in itertools.product(pool, repeat=3):
        steps = _simulate(list(combo))
        assert steps <= 3 + 3
