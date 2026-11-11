"""Pure football simulation domain."""

from brafoot.engine.lineups import (
    FORMATIONS,
    Lineup,
    LineupValidationError,
    LineupViolation,
    Starter,
    require_valid_lineup,
    validate_lineup,
)

__all__ = [
    "FORMATIONS",
    "Lineup",
    "LineupValidationError",
    "LineupViolation",
    "Starter",
    "require_valid_lineup",
    "validate_lineup",
]
