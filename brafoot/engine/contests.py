"""Deterministic head-to-head contests between player capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isclose

from brafoot.engine.attributes import (
    MAX_ATTRIBUTE_VALUE,
    MIN_ATTRIBUTE_VALUE,
    PlayerProfile,
)
from brafoot.engine.capabilities import (
    AerialPhase,
    DerivedAbility,
    SprintContext,
    calculate_aerial_ability,
    calculate_physical_duel_ability,
    calculate_sprint_ability,
)


class ContestOutcome(str, Enum):
    """Which side has the deterministic capability advantage."""

    FIRST = "first"
    SECOND = "second"
    EVEN = "even"


@dataclass(frozen=True, slots=True)
class ContestResult:
    """An explainable comparison that does not yet resolve a random event."""

    first: DerivedAbility
    second: DerivedAbility
    margin: float
    normalized_margin: float
    outcome: ContestOutcome


def compare_sprint(
    first: PlayerProfile,
    second: PlayerProfile,
    context: SprintContext,
) -> ContestResult:
    """Compare two players in a short or long straight-line run."""

    return compare_abilities(
        calculate_sprint_ability(first, context),
        calculate_sprint_ability(second, context),
    )


def compare_aerial_duel(
    attacker: PlayerProfile,
    defender: PlayerProfile,
) -> ContestResult:
    """Compare attacking and defensive aerial capabilities."""

    return compare_abilities(
        calculate_aerial_ability(attacker, AerialPhase.ATTACKING),
        calculate_aerial_ability(defender, AerialPhase.DEFENDING),
    )


def compare_physical_duel(
    first: PlayerProfile,
    second: PlayerProfile,
) -> ContestResult:
    """Compare two players in a ground contact dispute."""

    return compare_abilities(
        calculate_physical_duel_ability(first),
        calculate_physical_duel_ability(second),
    )


def compare_abilities(
    first: DerivedAbility,
    second: DerivedAbility,
) -> ContestResult:
    """Compare any two capabilities while preserving both explanations."""

    margin = first.score - second.score
    if isclose(margin, 0.0, abs_tol=1e-9):
        outcome = ContestOutcome.EVEN
        margin = 0.0
    elif margin > 0:
        outcome = ContestOutcome.FIRST
    else:
        outcome = ContestOutcome.SECOND

    scale_span = MAX_ATTRIBUTE_VALUE - MIN_ATTRIBUTE_VALUE
    normalized_margin = max(-1.0, min(1.0, margin / scale_span))
    return ContestResult(
        first=first,
        second=second,
        margin=margin,
        normalized_margin=normalized_margin,
        outcome=outcome,
    )
