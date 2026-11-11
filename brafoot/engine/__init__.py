"""Pure football simulation domain."""

from brafoot.engine.lineups import (
    AvailabilityStatus,
    FORMATIONS,
    Lineup,
    LineupValidationError,
    LineupViolation,
    Starter,
    require_valid_lineup,
    validate_lineup,
)
from brafoot.engine.matches import (
    MatchSetup,
    MatchSide,
    MatchValidationError,
    MatchViolation,
    require_valid_match,
    validate_match,
)

__all__ = [
    "AvailabilityStatus",
    "FORMATIONS",
    "Lineup",
    "LineupValidationError",
    "LineupViolation",
    "Starter",
    "require_valid_lineup",
    "validate_lineup",
    "MatchSetup",
    "MatchSide",
    "MatchValidationError",
    "MatchViolation",
    "require_valid_match",
    "validate_match",
]
