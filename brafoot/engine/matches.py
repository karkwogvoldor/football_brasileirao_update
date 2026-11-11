"""Domain rules for preparing a football match."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from brafoot.engine.lineups import Lineup, LineupViolation, validate_lineup


class MatchSide(str, Enum):
    """The side occupied by a club in a match."""

    HOME = "home"
    AWAY = "away"


@dataclass(frozen=True, slots=True)
class MatchSetup:
    """The two lineups submitted before a match starts."""

    home_lineup: Lineup
    away_lineup: Lineup


@dataclass(frozen=True, slots=True)
class MatchViolation:
    """A stable match validation error for application adapters."""

    code: str
    message: str
    side: MatchSide | None = None
    lineup_violations: tuple[LineupViolation, ...] = ()


class MatchValidationError(ValueError):
    """Raised when a match cannot start."""

    def __init__(self, violations: tuple[MatchViolation, ...]) -> None:
        self.violations = violations
        super().__init__("; ".join(violation.message for violation in violations))


def validate_match(match: MatchSetup) -> tuple[MatchViolation, ...]:
    """Return every rule violation that prevents the match from starting."""

    violations: list[MatchViolation] = []

    if match.home_lineup.club_id == match.away_lineup.club_id:
        violations.append(
            MatchViolation(
                code="clubs_must_differ",
                message="Mandante e visitante devem ser clubes diferentes.",
            )
        )

    for side, lineup in (
        (MatchSide.HOME, match.home_lineup),
        (MatchSide.AWAY, match.away_lineup),
    ):
        lineup_violations = validate_lineup(lineup)
        if lineup_violations:
            violations.append(
                MatchViolation(
                    code=f"invalid_{side.value}_lineup",
                    message=(
                        "A escalação do mandante não é válida."
                        if side is MatchSide.HOME
                        else "A escalação do visitante não é válida."
                    ),
                    side=side,
                    lineup_violations=lineup_violations,
                )
            )

    return tuple(violations)


def require_valid_match(match: MatchSetup) -> None:
    """Raise a domain error when the match cannot start."""

    violations = validate_match(match)
    if violations:
        raise MatchValidationError(violations)
