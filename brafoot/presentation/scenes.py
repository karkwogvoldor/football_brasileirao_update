"""Versioned visual scenes that cannot alter confirmed sport outcomes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from brafoot.engine.events import MatchEvent, MatchEventType
from brafoot.engine.matches import MatchSide


DEFAULT_PRESENTATION_VERSION = "2026.1"
PASS_SCENE_DURATION_MS = 1200


@dataclass(frozen=True, slots=True)
class NormalizedPoint:
    """One resolution-independent position on the presentation field."""

    x: float
    y: float

    def __post_init__(self) -> None:
        if not _is_normalized_number(self.x) or not _is_normalized_number(self.y):
            raise ValueError("As coordenadas da apresentação devem estar entre 0 e 100.")


@dataclass(frozen=True, slots=True)
class SceneKeyframe:
    """The ball position at one deterministic instant of a visual scene."""

    at_ms: int
    position: NormalizedPoint

    def __post_init__(self) -> None:
        if not _is_non_negative_int(self.at_ms):
            raise ValueError("O instante do keyframe deve ser um inteiro não negativo.")
        if not isinstance(self.position, NormalizedPoint):
            raise ValueError("A posição do keyframe não é válida.")


@dataclass(frozen=True, slots=True)
class PresentationScene:
    """A persistable visual interpretation of one confirmed match event."""

    presentation_version: str
    event_sequence: int
    event_type: MatchEventType
    team_side: MatchSide
    participant_ids: tuple[int, ...]
    duration_ms: int
    keyframes: tuple[SceneKeyframe, ...]
    narration: str

    def __post_init__(self) -> None:
        if not _is_canonical_code(self.presentation_version):
            raise ValueError("A versão da apresentação não é válida.")
        if not _is_positive_int(self.event_sequence):
            raise ValueError("A sequência do evento da cena não é válida.")
        if not isinstance(self.event_type, MatchEventType):
            raise ValueError("O tipo do evento da cena não é válido.")
        if not isinstance(self.team_side, MatchSide):
            raise ValueError("O lado da cena não é válido.")
        if (
            not isinstance(self.participant_ids, tuple)
            or not self.participant_ids
            or not all(_is_positive_int(item) for item in self.participant_ids)
            or len(set(self.participant_ids)) != len(self.participant_ids)
        ):
            raise ValueError("Os participantes da cena não são válidos.")
        if not _is_positive_int(self.duration_ms):
            raise ValueError("A duração da cena deve ser um inteiro positivo.")
        if (
            not isinstance(self.keyframes, tuple)
            or len(self.keyframes) < 2
            or not all(isinstance(frame, SceneKeyframe) for frame in self.keyframes)
        ):
            raise ValueError("A cena deve conter keyframes válidos.")
        if self.keyframes[0].at_ms != 0 or self.keyframes[-1].at_ms != self.duration_ms:
            raise ValueError("Os keyframes devem cobrir toda a duração da cena.")
        if any(
            current.at_ms <= previous.at_ms
            for previous, current in zip(self.keyframes, self.keyframes[1:])
        ):
            raise ValueError("Os keyframes devem estar em ordem estritamente crescente.")
        if (
            not isinstance(self.narration, str)
            or not self.narration
            or self.narration.strip() != self.narration
        ):
            raise ValueError("A narração da cena não é válida.")

    def to_snapshot(self) -> dict[str, object]:
        """Return a JSON-compatible representation for APIs and replays."""

        return {
            "presentation_version": self.presentation_version,
            "event_sequence": self.event_sequence,
            "event_type": self.event_type.value,
            "team_side": self.team_side.value,
            "participant_ids": list(self.participant_ids),
            "duration_ms": self.duration_ms,
            "keyframes": [
                {
                    "at_ms": frame.at_ms,
                    "x": frame.position.x,
                    "y": frame.position.y,
                }
                for frame in self.keyframes
            ],
            "narration": self.narration,
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, object]) -> PresentationScene:
        """Restore and validate a scene from its explicit representation."""

        if not isinstance(snapshot, Mapping):
            raise ValueError("O snapshot da cena não é válido.")
        try:
            participant_ids = snapshot["participant_ids"]
            keyframes = snapshot["keyframes"]
            if not isinstance(participant_ids, list) or not isinstance(keyframes, list):
                raise ValueError
            return cls(
                presentation_version=snapshot["presentation_version"],
                event_sequence=snapshot["event_sequence"],
                event_type=MatchEventType(snapshot["event_type"]),
                team_side=MatchSide(snapshot["team_side"]),
                participant_ids=tuple(participant_ids),
                duration_ms=snapshot["duration_ms"],
                keyframes=tuple(_keyframe_from_snapshot(frame) for frame in keyframes),
                narration=snapshot["narration"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("O snapshot da cena não é válido.") from error


def build_pass_scene(
    event: MatchEvent,
    *,
    participant_positions: Mapping[int, NormalizedPoint],
    presentation_version: str = DEFAULT_PRESENTATION_VERSION,
) -> PresentationScene:
    """Create deterministic ball keyframes from one confirmed pass event."""

    if not isinstance(event, MatchEvent):
        raise ValueError("O evento da cena de passe não é válido.")
    if event.event_type is not MatchEventType.PASS:
        raise ValueError("A cena de passe exige um evento do tipo passe.")
    if len(event.participant_ids) != 2:
        raise ValueError("A cena de passe exige exatamente dois participantes.")
    if event.origin_zone is None or event.destination_zone is None:
        raise ValueError("A cena de passe exige zonas de origem e destino.")
    assert event.team_side is not None
    if not isinstance(participant_positions, Mapping):
        raise ValueError("As posições dos participantes do passe não são válidas.")
    try:
        start = participant_positions[event.participant_ids[0]]
        end = participant_positions[event.participant_ids[1]]
    except KeyError as error:
        raise ValueError(
            "A cena de passe exige as posições dos participantes A e B."
        ) from error
    if not isinstance(start, NormalizedPoint) or not isinstance(end, NormalizedPoint):
        raise ValueError("As posições dos participantes do passe não são válidas.")

    midpoint = NormalizedPoint(
        x=(start.x + end.x) / 2,
        y=(start.y + end.y) / 2,
    )
    return PresentationScene(
        presentation_version=presentation_version,
        event_sequence=event.sequence,
        event_type=event.event_type,
        team_side=event.team_side,
        participant_ids=event.participant_ids,
        duration_ms=PASS_SCENE_DURATION_MS,
        keyframes=tuple(
            SceneKeyframe(at_ms=at_ms, position=point)
            for at_ms, point in zip(
                (0, 600, PASS_SCENE_DURATION_MS),
                (start, midpoint, end),
            )
        ),
        narration=event.explanation,
    )


def _keyframe_from_snapshot(snapshot: object) -> SceneKeyframe:
    if not isinstance(snapshot, Mapping):
        raise ValueError
    return SceneKeyframe(
        at_ms=snapshot["at_ms"],
        position=NormalizedPoint(x=snapshot["x"], y=snapshot["y"]),
    )


def _is_normalized_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0 <= value <= 100
    )


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_canonical_code(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value
