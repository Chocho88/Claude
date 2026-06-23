"""The pure routing decision. No I/O, no LLM — exhaustively unit-tested.

This is the only place the loop's control flow is decided, so termination is a
property of one small function:

  * Within a phase, re-synthesize from the same bites at most
    `max_synth_per_phase` times.
  * When that budget is spent, spend at most `max_escalations` escalation:
    EVIDENCE_GAP -> Retrieval, INTENT_OR_STRATEGY -> Planning. An escalation
    resets the synth budget (a fresh phase) and increments `escalations_used`.
  * Otherwise ship the best draft seen, with a caveat.

Every non-terminal decision strictly increments a bounded counter, so the loop
cannot run forever.
"""

from __future__ import annotations

from enum import Enum

from r2a.domain.reflection import ReflectionResult
from r2a.domain.trace import IssueType, RoutingTarget

from .stage import RunCounters


class Decision(str, Enum):
    SHIP = "SHIP"  # Reflection is satisfied
    RESYNTH = "RESYNTH"  # try again from the same bites
    ESCALATE_RETRIEVAL = "ESCALATE_RETRIEVAL"  # widen evidence, then re-synth
    ESCALATE_PLANNING = "ESCALATE_PLANNING"  # re-plan intent, then re-synth
    SHIP_BEST = "SHIP_BEST"  # budgets spent; ship best-scoring draft + caveat


def decide(
    reflection: ReflectionResult,
    counters: RunCounters,
    *,
    max_synth_per_phase: int = 3,
    max_escalations: int = 1,
) -> Decision:
    if reflection.routing_target == RoutingTarget.SHIP:
        return Decision.SHIP

    # Still have re-synthesis budget in this phase.
    if counters.synth_attempts < max_synth_per_phase:
        return Decision.RESYNTH

    # Budget spent — escalate once if we still can and the issue is escalable.
    if counters.escalations_used < max_escalations:
        if reflection.issue_type == IssueType.EVIDENCE_GAP:
            return Decision.ESCALATE_RETRIEVAL
        if reflection.issue_type == IssueType.INTENT_OR_STRATEGY:
            return Decision.ESCALATE_PLANNING
        # FORMAT / NONE with no synth budget left: nothing productive remains.

    return Decision.SHIP_BEST
