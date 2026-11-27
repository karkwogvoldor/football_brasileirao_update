"""Versioned visual scenes that cannot alter confirmed sport outcomes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from brafoot.engine.events import MatchEvent, MatchEventType
from brafoot.engine.matches import MatchSide


DEFAULT_PRESENTATION_VERSION = "2026.1"
PASS_SCENE_DURATION_MS = 1200
CARRY_SCENE_DURATION_MS = 1400
SHOT_SCENE_DURATION_MS = 900


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
    """One entity position at a deterministic instant of a visual scene."""

    at_ms: int
    position: NormalizedPoint

    def __post_init__(self) -> None:
        if not _is_non_negative_int(self.at_ms):
            raise ValueError("O instante do keyframe deve ser um inteiro não negativo.")
        if not isinstance(self.position, NormalizedPoint):
            raise ValueError("A posição do keyframe não é válida.")


@dataclass(frozen=True, slots=True)
class PlayerTrack:
    """One player's complete movement during a visual scene."""

    side: MatchSide
    player_id: int
    keyframes: tuple[SceneKeyframe, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.side, MatchSide):
            raise ValueError("O lado da trilha do jogador não é válido.")
        if not _is_positive_int(self.player_id):
            raise ValueError("O jogador da trilha não é válido.")
        _validate_keyframes(self.keyframes)


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
    player_tracks: tuple[PlayerTrack, ...]
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
        _validate_keyframes(self.keyframes)
        if self.keyframes[0].at_ms != 0 or self.keyframes[-1].at_ms != self.duration_ms:
            raise ValueError("Os keyframes devem cobrir toda a duração da cena.")
        if not isinstance(self.player_tracks, tuple) or not all(
            isinstance(track, PlayerTrack) for track in self.player_tracks
        ):
            raise ValueError("As trilhas dos jogadores não são válidas.")
        track_identities = tuple(
            (track.side, track.player_id) for track in self.player_tracks
        )
        if len(set(track_identities)) != len(track_identities):
            raise ValueError("As trilhas dos jogadores devem ser únicas.")
        if any(
            track.keyframes[0].at_ms != 0
            or track.keyframes[-1].at_ms != self.duration_ms
            for track in self.player_tracks
        ):
            raise ValueError("As trilhas devem cobrir toda a duração da cena.")
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
            "player_tracks": [
                {
                    "side": track.side.value,
                    "player_id": track.player_id,
                    "keyframes": [
                        {
                            "at_ms": frame.at_ms,
                            "x": frame.position.x,
                            "y": frame.position.y,
                        }
                        for frame in track.keyframes
                    ],
                }
                for track in self.player_tracks
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
            player_tracks = snapshot["player_tracks"]
            if (
                not isinstance(participant_ids, list)
                or not isinstance(keyframes, list)
                or not isinstance(player_tracks, list)
            ):
                raise ValueError
            return cls(
                presentation_version=snapshot["presentation_version"],
                event_sequence=snapshot["event_sequence"],
                event_type=MatchEventType(snapshot["event_type"]),
                team_side=MatchSide(snapshot["team_side"]),
                participant_ids=tuple(participant_ids),
                duration_ms=snapshot["duration_ms"],
                keyframes=tuple(_keyframe_from_snapshot(frame) for frame in keyframes),
                player_tracks=tuple(
                    _player_track_from_snapshot(track) for track in player_tracks
                ),
                narration=snapshot["narration"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("O snapshot da cena não é válido.") from error


def build_pass_scene(
    event: MatchEvent,
    *,
    participant_positions: Mapping[int, NormalizedPoint],
    player_movements: Mapping[
        tuple[MatchSide, int], tuple[NormalizedPoint, NormalizedPoint]
    ]
    | None = None,
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
        player_tracks=_build_player_tracks(
            player_movements,
            PASS_SCENE_DURATION_MS,
        ),
        narration=event.explanation,
    )


def build_carry_scene(
    event: MatchEvent,
    *,
    start_position: NormalizedPoint,
    destination_position: NormalizedPoint,
    player_movements: Mapping[
        tuple[MatchSide, int], tuple[NormalizedPoint, NormalizedPoint]
    ]
    | None = None,
    presentation_version: str = DEFAULT_PRESENTATION_VERSION,
) -> PresentationScene:
    """Create matching player and ball tracks for one confirmed carry."""

    if not isinstance(event, MatchEvent):
        raise ValueError("O evento da cena de condução não é válido.")
    if event.event_type is not MatchEventType.CARRY:
        raise ValueError("A cena de condução exige um evento do tipo condução.")
    if len(event.participant_ids) != 1:
        raise ValueError("A cena de condução exige exatamente um participante.")
    if event.origin_zone is None or event.destination_zone is None:
        raise ValueError("A cena de condução exige zonas de origem e destino.")
    if not isinstance(start_position, NormalizedPoint) or not isinstance(
        destination_position, NormalizedPoint
    ):
        raise ValueError("As posições da condução não são válidas.")
    assert event.team_side is not None

    midpoint = NormalizedPoint(
        x=(start_position.x + destination_position.x) / 2,
        y=(start_position.y + destination_position.y) / 2,
    )
    keyframes = tuple(
        SceneKeyframe(at_ms=at_ms, position=point)
        for at_ms, point in zip(
            (0, CARRY_SCENE_DURATION_MS // 2, CARRY_SCENE_DURATION_MS),
            (start_position, midpoint, destination_position),
        )
    )
    carrier_identity = (event.team_side, event.participant_ids[0])
    movements = player_movements or {
        carrier_identity: (start_position, destination_position)
    }
    if not isinstance(movements, Mapping) or movements.get(carrier_identity) != (
        start_position,
        destination_position,
    ):
        raise ValueError("Os movimentos coletivos devem incluir a condução do portador.")
    return PresentationScene(
        presentation_version=presentation_version,
        event_sequence=event.sequence,
        event_type=event.event_type,
        team_side=event.team_side,
        participant_ids=event.participant_ids,
        duration_ms=CARRY_SCENE_DURATION_MS,
        keyframes=keyframes,
        player_tracks=_build_player_tracks(
            movements,
            CARRY_SCENE_DURATION_MS,
        ),
        narration=event.explanation,
    )


def build_shot_scene(
    event: MatchEvent,
    *,
    start_position: NormalizedPoint,
    target_position: NormalizedPoint,
    player_movements: Mapping[
        tuple[MatchSide, int], tuple[NormalizedPoint, NormalizedPoint]
    ]
    | None = None,
    presentation_version: str = DEFAULT_PRESENTATION_VERSION,
) -> PresentationScene:
    """Create the ball track for one confirmed shot toward an exact target."""

    if not isinstance(event, MatchEvent):
        raise ValueError("O evento da cena de finalização não é válido.")
    if event.event_type is not MatchEventType.SHOT:
        raise ValueError("A cena de finalização exige um evento de finalização.")
    if len(event.participant_ids) != 1:
        raise ValueError("A cena de finalização exige exatamente um participante.")
    if event.origin_zone is None or event.destination_zone is None:
        raise ValueError("A cena de finalização exige zonas de origem e destino.")
    if not isinstance(start_position, NormalizedPoint) or not isinstance(
        target_position, NormalizedPoint
    ):
        raise ValueError("As posições da finalização não são válidas.")
    assert event.team_side is not None

    midpoint = NormalizedPoint(
        x=(start_position.x + target_position.x) / 2,
        y=(start_position.y + target_position.y) / 2,
    )
    return PresentationScene(
        presentation_version=presentation_version,
        event_sequence=event.sequence,
        event_type=event.event_type,
        team_side=event.team_side,
        participant_ids=event.participant_ids,
        duration_ms=SHOT_SCENE_DURATION_MS,
        keyframes=tuple(
            SceneKeyframe(at_ms=at_ms, position=point)
            for at_ms, point in zip(
                (0, SHOT_SCENE_DURATION_MS // 2, SHOT_SCENE_DURATION_MS),
                (start_position, midpoint, target_position),
            )
        ),
        player_tracks=_build_player_tracks(
            player_movements,
            SHOT_SCENE_DURATION_MS,
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


def _player_track_from_snapshot(snapshot: object) -> PlayerTrack:
    if not isinstance(snapshot, Mapping):
        raise ValueError
    keyframes = snapshot["keyframes"]
    if not isinstance(keyframes, list):
        raise ValueError
    return PlayerTrack(
        side=MatchSide(snapshot["side"]),
        player_id=snapshot["player_id"],
        keyframes=tuple(_keyframe_from_snapshot(frame) for frame in keyframes),
    )


def _validate_keyframes(keyframes: object) -> None:
    if (
        not isinstance(keyframes, tuple)
        or len(keyframes) < 2
        or not all(isinstance(frame, SceneKeyframe) for frame in keyframes)
    ):
        raise ValueError("A cena deve conter keyframes válidos.")
    if any(
        current.at_ms <= previous.at_ms
        for previous, current in zip(keyframes, keyframes[1:])
    ):
        raise ValueError("Os keyframes devem estar em ordem estritamente crescente.")


def _build_player_tracks(
    movements: Mapping[
        tuple[MatchSide, int], tuple[NormalizedPoint, NormalizedPoint]
    ]
    | None,
    duration_ms: int,
) -> tuple[PlayerTrack, ...]:
    if movements is None:
        return ()
    if not isinstance(movements, Mapping):
        raise ValueError("Os movimentos coletivos da cena não são válidos.")

    tracks = []
    for identity, positions in movements.items():
        if (
            not isinstance(identity, tuple)
            or len(identity) != 2
            or not isinstance(identity[0], MatchSide)
            or not _is_positive_int(identity[1])
            or not isinstance(positions, tuple)
            or len(positions) != 2
            or not all(isinstance(point, NormalizedPoint) for point in positions)
        ):
            raise ValueError("Os movimentos coletivos da cena não são válidos.")
        start, end = positions
        midpoint = NormalizedPoint(
            x=(start.x + end.x) / 2,
            y=(start.y + end.y) / 2,
        )
        tracks.append(
            PlayerTrack(
                side=identity[0],
                player_id=identity[1],
                keyframes=tuple(
                    SceneKeyframe(at_ms=at_ms, position=point)
                    for at_ms, point in zip(
                        (0, duration_ms // 2, duration_ms),
                        (start, midpoint, end),
                    )
                ),
            )
        )
    return tuple(tracks)


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
