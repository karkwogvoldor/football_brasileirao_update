"""Semantic, persistable match events and deterministic timeline rules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from brafoot.engine.clock import MatchClock, MatchPeriod
from brafoot.engine.matches import MatchSide
from brafoot.engine.zones import FieldZone


class MatchEventType(str, Enum):
    """Stable semantic event categories produced by the match engine."""

    PERIOD_START = "period_start"
    PERIOD_END = "period_end"
    POSSESSION_CHANGE = "possession_change"
    PASS = "pass"
    CARRY = "carry"
    DUEL = "duel"
    CROSS = "cross"
    SHOT = "shot"
    SAVE = "save"
    GOAL = "goal"
    FOUL = "foul"
    CARD = "card"
    SUBSTITUTION = "substitution"


NEUTRAL_EVENT_TYPES = frozenset(
    {MatchEventType.PERIOD_START, MatchEventType.PERIOD_END}
)


@dataclass(frozen=True, slots=True)
class MatchEvent:
    """The common immutable envelope shared by semantic match events."""

    sequence: int
    clock: MatchClock
    event_type: MatchEventType
    team_side: MatchSide | None
    participant_ids: tuple[int, ...]
    origin_zone: FieldZone | None
    destination_zone: FieldZone | None
    context: str | None
    outcome: str | None
    explanation: str

    def __post_init__(self) -> None:
        if not _is_positive_int(self.sequence):
            raise ValueError("A sequência do evento deve ser um inteiro positivo.")
        if not isinstance(self.clock, MatchClock):
            raise ValueError("O relógio do evento não é válido.")
        if not isinstance(self.event_type, MatchEventType):
            raise ValueError("O tipo do evento não é válido.")
        self._validate_team_side()
        if (
            not isinstance(self.participant_ids, tuple)
            or not all(_is_positive_int(item) for item in self.participant_ids)
            or len(set(self.participant_ids)) != len(self.participant_ids)
        ):
            raise ValueError(
                "Os participantes do evento devem ser IDs únicos e positivos."
            )
        if self.origin_zone is not None and not isinstance(
            self.origin_zone, FieldZone
        ):
            raise ValueError("A zona de origem do evento não é válida.")
        if self.destination_zone is not None and not isinstance(
            self.destination_zone, FieldZone
        ):
            raise ValueError("A zona de destino do evento não é válida.")
        if not _is_optional_canonical_code(self.context):
            raise ValueError("O contexto do evento não é válido.")
        if not _is_optional_canonical_code(self.outcome):
            raise ValueError("O resultado do evento não é válido.")
        if (
            not isinstance(self.explanation, str)
            or not self.explanation.strip()
            or self.explanation.strip() != self.explanation
        ):
            raise ValueError("A explicação do evento não é válida.")

    def _validate_team_side(self) -> None:
        if self.event_type in NEUTRAL_EVENT_TYPES:
            if (
                self.team_side is not None
                or self.participant_ids
                or self.origin_zone is not None
                or self.destination_zone is not None
                or self.context is not None
                or self.outcome is not None
            ):
                raise ValueError(
                    "Eventos de período não podem conter carga esportiva."
                )
            return
        if not isinstance(self.team_side, MatchSide):
            raise ValueError("O evento esportivo deve informar uma equipe válida.")

    def to_snapshot(self) -> dict[str, object]:
        """Return an explicit JSON-compatible representation of this event."""

        return {
            "sequence": self.sequence,
            "elapsed_seconds": self.clock.elapsed_seconds,
            "period": self.clock.period.value,
            "event_type": self.event_type.value,
            "team_side": self.team_side.value if self.team_side else None,
            "participant_ids": list(self.participant_ids),
            "origin_zone": self.origin_zone.code if self.origin_zone else None,
            "destination_zone": (
                self.destination_zone.code if self.destination_zone else None
            ),
            "context": self.context,
            "outcome": self.outcome,
            "explanation": self.explanation,
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, object]) -> MatchEvent:
        """Restore and validate an event from its persisted representation."""

        if not isinstance(snapshot, Mapping):
            raise ValueError("O snapshot do evento não é válido.")
        try:
            participant_ids = snapshot["participant_ids"]
            if not isinstance(participant_ids, list):
                raise ValueError("Os participantes persistidos não são válidos.")

            team_value = snapshot["team_side"]
            origin_value = snapshot["origin_zone"]
            destination_value = snapshot["destination_zone"]
            return cls(
                sequence=snapshot["sequence"],
                clock=MatchClock(
                    elapsed_seconds=snapshot["elapsed_seconds"],
                    period=MatchPeriod(snapshot["period"]),
                ),
                event_type=MatchEventType(snapshot["event_type"]),
                team_side=MatchSide(team_value) if team_value is not None else None,
                participant_ids=tuple(participant_ids),
                origin_zone=(
                    FieldZone.from_code(origin_value)
                    if origin_value is not None
                    else None
                ),
                destination_zone=(
                    FieldZone.from_code(destination_value)
                    if destination_value is not None
                    else None
                ),
                context=snapshot["context"],
                outcome=snapshot["outcome"],
                explanation=snapshot["explanation"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("O snapshot do evento não é válido.") from error


@dataclass(frozen=True, slots=True)
class EventTimelineViolation:
    """A stable ordering violation found between two confirmed events."""

    code: str
    event_sequence: int
    message: str


def validate_event_timeline(
    events: tuple[MatchEvent, ...],
) -> tuple[EventTimelineViolation, ...]:
    """Validate sequence and chronological order without reordering events."""

    if not isinstance(events, tuple) or not all(
        isinstance(event, MatchEvent) for event in events
    ):
        raise ValueError("A timeline deve ser uma tupla de eventos válidos.")

    violations: list[EventTimelineViolation] = []
    for previous, current in zip(events, events[1:]):
        if current.sequence != previous.sequence + 1:
            violations.append(
                EventTimelineViolation(
                    code="non_contiguous_event_sequence",
                    event_sequence=current.sequence,
                    message="A sequência dos eventos deve avançar de um em um.",
                )
            )

        if current.clock.elapsed_seconds < previous.clock.elapsed_seconds:
            violations.append(
                EventTimelineViolation(
                    code="event_clock_moved_backwards",
                    event_sequence=current.sequence,
                    message="O relógio dos eventos não pode retroceder.",
                )
            )
        elif (
            current.clock.elapsed_seconds == previous.clock.elapsed_seconds
            and _period_order(current.clock.period)
            < _period_order(previous.clock.period)
        ):
            violations.append(
                EventTimelineViolation(
                    code="event_period_moved_backwards",
                    event_sequence=current.sequence,
                    message="O período dos eventos não pode retroceder.",
                )
            )

    return tuple(violations)


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_optional_canonical_code(value: object) -> bool:
    return value is None or (
        isinstance(value, str) and bool(value) and value.strip() == value
    )


def _period_order(period: MatchPeriod) -> int:
    return {
        MatchPeriod.FIRST_HALF: 0,
        MatchPeriod.HALF_TIME: 1,
        MatchPeriod.SECOND_HALF: 2,
        MatchPeriod.FULL_TIME: 3,
    }[period]
