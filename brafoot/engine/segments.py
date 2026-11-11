"""Pure advancement of match segments without sport events."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from brafoot.engine.clock import MatchPeriod, advance_match_clock
from brafoot.engine.rulesets import SimulationRuleset
from brafoot.engine.state import MatchState


class SegmentStopReason(str, Enum):
    """The deterministic boundary that ended a segment advance."""

    DURATION_LIMIT = "duration_limit"
    HALF_TIME = "half_time"
    FULL_TIME = "full_time"


@dataclass(frozen=True, slots=True)
class SegmentAdvance:
    """The immutable result of advancing one event-free match segment."""

    start_state: MatchState
    end_state: MatchState
    elapsed_seconds: int
    stop_reason: SegmentStopReason


def advance_match_segment(
    state: MatchState,
    ruleset: SimulationRuleset,
) -> SegmentAdvance:
    """Advance only the clock up to duration, half-time, or full-time."""

    if not isinstance(state, MatchState):
        raise ValueError("O estado da partida não é válido.")
    if not isinstance(ruleset, SimulationRuleset):
        raise ValueError("O conjunto de regras não é válido.")
    if state.ruleset_version != ruleset.version:
        raise ValueError("A versão do ruleset não corresponde ao estado da partida.")
    if state.clock.period not in {
        MatchPeriod.FIRST_HALF,
        MatchPeriod.SECOND_HALF,
    }:
        raise ValueError("O período atual não permite avançar um segmento.")

    end_clock = advance_match_clock(
        state.clock,
        ruleset.segment_duration_seconds,
    )
    end_state = replace(state, clock=end_clock)

    if end_clock.period is MatchPeriod.HALF_TIME:
        stop_reason = SegmentStopReason.HALF_TIME
    elif end_clock.period is MatchPeriod.FULL_TIME:
        stop_reason = SegmentStopReason.FULL_TIME
    else:
        stop_reason = SegmentStopReason.DURATION_LIMIT

    return SegmentAdvance(
        start_state=state,
        end_state=end_state,
        elapsed_seconds=end_clock.elapsed_seconds - state.clock.elapsed_seconds,
        stop_reason=stop_reason,
    )
