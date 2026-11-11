"""Pure domain rules for the regulation match clock."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


REGULATION_HALF_SECONDS = 45 * 60
REGULATION_MATCH_SECONDS = 2 * REGULATION_HALF_SECONDS


class MatchPeriod(str, Enum):
    """The regulation period represented by a match clock state."""

    FIRST_HALF = "first_half"
    HALF_TIME = "half_time"
    SECOND_HALF = "second_half"
    FULL_TIME = "full_time"


@dataclass(frozen=True, slots=True)
class MatchClock:
    """An immutable regulation clock whose elapsed time is globally monotonic."""

    elapsed_seconds: int
    period: MatchPeriod

    def __post_init__(self) -> None:
        if not _is_valid_elapsed_seconds(self.elapsed_seconds):
            raise ValueError("O segundo atual deve ser um inteiro não negativo.")
        if not isinstance(self.period, MatchPeriod):
            raise ValueError("O período da partida não é válido.")
        if not _is_consistent_period(self.elapsed_seconds, self.period):
            raise ValueError("O segundo atual não é compatível com o período.")

    @classmethod
    def start(cls) -> MatchClock:
        """Return the initial clock state of a regulation match."""

        return cls(elapsed_seconds=0, period=MatchPeriod.FIRST_HALF)

    @property
    def minute(self) -> int:
        """Return the continuous displayed match minute."""

        return self.elapsed_seconds // 60

    @property
    def second_in_minute(self) -> int:
        """Return the displayed second inside the current match minute."""

        return self.elapsed_seconds % 60

    @property
    def display(self) -> str:
        """Return a deterministic MM:SS representation for presentation layers."""

        return f"{self.minute:02d}:{self.second_in_minute:02d}"


def advance_match_clock(clock: MatchClock, seconds: int) -> MatchClock:
    """Advance within the current half and stop at the next regulation boundary."""

    if not _is_valid_elapsed_seconds(seconds):
        raise ValueError("A duração do avanço deve ser um inteiro não negativo.")
    if seconds == 0 or clock.period in {
        MatchPeriod.HALF_TIME,
        MatchPeriod.FULL_TIME,
    }:
        return clock

    boundary = (
        REGULATION_HALF_SECONDS
        if clock.period is MatchPeriod.FIRST_HALF
        else REGULATION_MATCH_SECONDS
    )
    elapsed_seconds = min(clock.elapsed_seconds + seconds, boundary)

    if elapsed_seconds == REGULATION_HALF_SECONDS:
        period = MatchPeriod.HALF_TIME
    elif elapsed_seconds == REGULATION_MATCH_SECONDS:
        period = MatchPeriod.FULL_TIME
    else:
        period = clock.period

    return MatchClock(elapsed_seconds=elapsed_seconds, period=period)


def start_second_half(clock: MatchClock) -> MatchClock:
    """Resume a match from its explicit half-time state."""

    if clock.period is not MatchPeriod.HALF_TIME:
        raise ValueError("O segundo tempo somente pode iniciar durante o intervalo.")
    return MatchClock(
        elapsed_seconds=clock.elapsed_seconds,
        period=MatchPeriod.SECOND_HALF,
    )


def _is_valid_elapsed_seconds(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_consistent_period(elapsed_seconds: int, period: MatchPeriod) -> bool:
    if period is MatchPeriod.FIRST_HALF:
        return elapsed_seconds < REGULATION_HALF_SECONDS
    if period is MatchPeriod.HALF_TIME:
        return elapsed_seconds == REGULATION_HALF_SECONDS
    if period is MatchPeriod.SECOND_HALF:
        return REGULATION_HALF_SECONDS <= elapsed_seconds < REGULATION_MATCH_SECONDS
    return elapsed_seconds == REGULATION_MATCH_SECONDS
