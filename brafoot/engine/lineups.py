"""Domain rules for a starting football lineup."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


FORMATIONS: dict[str, tuple[int, ...]] = {
    "4-1-2-1-2": (4, 1, 2, 1, 2),
    "4-4-2": (4, 4, 2),
    "4-3-3": (4, 3, 3),
    "3-4-3": (3, 4, 3),
    "4-2-3-1": (4, 2, 3, 1),
    "3-5-2": (3, 5, 2),
}


class AvailabilityStatus(str, Enum):
    """A player's eligibility state for the next match."""

    AVAILABLE = "available"
    INJURED = "injured"
    SUSPENDED = "suspended"


@dataclass(frozen=True, slots=True)
class Starter:
    """Minimal player data required to validate a lineup."""

    player_id: int
    club_id: int
    position: str
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE


@dataclass(frozen=True, slots=True)
class Lineup:
    """A club's starting eleven and tactical formation."""

    club_id: int
    formation: str
    starters: tuple[Starter, ...]


@dataclass(frozen=True, slots=True)
class LineupViolation:
    """A stable rule violation that can be exposed by any adapter."""

    code: str
    message: str
    player_ids: tuple[int, ...] = ()


class LineupValidationError(ValueError):
    """Raised when a lineup violates one or more domain rules."""

    def __init__(self, violations: tuple[LineupViolation, ...]) -> None:
        self.violations = violations
        super().__init__("; ".join(violation.message for violation in violations))


def validate_lineup(lineup: Lineup) -> tuple[LineupViolation, ...]:
    """Return every violated starting-lineup rule in deterministic order."""

    violations: list[LineupViolation] = []
    player_ids = [starter.player_id for starter in lineup.starters]
    goalkeeper_count = sum(
        starter.position.strip().upper() == "GOL" for starter in lineup.starters
    )

    if len(lineup.starters) != 11:
        violations.append(
            LineupViolation(
                code="starter_count",
                message="A escalação deve ter exatamente 11 titulares.",
            )
        )

    if len(set(player_ids)) != len(player_ids):
        violations.append(
            LineupViolation(
                code="duplicate_player",
                message="Os 11 titulares devem ser jogadores distintos.",
            )
        )

    if goalkeeper_count != 1:
        violations.append(
            LineupViolation(
                code="goalkeeper_count",
                message="A escalação deve ter exatamente um goleiro.",
            )
        )

    if any(starter.club_id != lineup.club_id for starter in lineup.starters):
        violations.append(
            LineupViolation(
                code="foreign_player",
                message="Todos os titulares devem estar vinculados ao clube.",
            )
        )

    ineligible_player_ids = tuple(
        starter.player_id
        for starter in lineup.starters
        if starter.availability != AvailabilityStatus.AVAILABLE
    )
    if ineligible_player_ids:
        violations.append(
            LineupViolation(
                code="ineligible_player",
                message="Jogadores lesionados ou suspensos não podem ser titulares.",
                player_ids=ineligible_player_ids,
            )
        )

    formation_lines = FORMATIONS.get(lineup.formation)
    if formation_lines is None or sum(formation_lines) != 10:
        violations.append(
            LineupViolation(
                code="invalid_formation",
                message="A formação tática não é válida.",
            )
        )

    return tuple(violations)


def require_valid_lineup(lineup: Lineup) -> None:
    """Raise a domain error when the lineup is not valid."""

    violations = validate_lineup(lineup)
    if violations:
        raise LineupValidationError(violations)
