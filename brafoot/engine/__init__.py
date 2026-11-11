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

__all__ = [
    "AvailabilityStatus",
    "FORMATIONS",
    "Lineup",
    "LineupValidationError",
    "LineupViolation",
    "Starter",
    "require_valid_lineup",
    "validate_lineup",
]
