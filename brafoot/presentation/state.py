"""Immutable visual state advanced by scenes derived from confirmed events."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from brafoot.engine.events import MatchEvent, MatchEventType
from brafoot.engine.matches import MatchSide
from brafoot.presentation.scenes import (
    NormalizedPoint,
    PresentationScene,
    build_carry_scene,
    build_pass_scene,
    build_shot_scene,
)

CARRY_BLOCK_PROGRESS_RATIO = 0.5
CARRY_BLOCK_LATERAL_RATIO = 0.15
MAX_CARRY_BLOCK_PROGRESS = 6
MAX_CARRY_BLOCK_LATERAL = 3


@dataclass(frozen=True, slots=True)
class PresentedPlayer:
    """One player's identity and current position in the visual layer."""

    side: MatchSide
    player_id: int
    position: NormalizedPoint

    def __post_init__(self) -> None:
        if not isinstance(self.side, MatchSide):
            raise ValueError("O lado do jogador apresentado não é válido.")
        if not _is_positive_int(self.player_id):
            raise ValueError("O ID do jogador apresentado não é válido.")
        if not isinstance(self.position, NormalizedPoint):
            raise ValueError("A posição do jogador apresentado não é válida.")


@dataclass(frozen=True, slots=True)
class PresentationState:
    """The complete visual boundary between two presentation scenes."""

    presentation_version: str
    players: tuple[PresentedPlayer, ...]
    ball_position: NormalizedPoint
    ball_holder_side: MatchSide | None
    ball_holder_id: int | None
    last_event_sequence: int | None

    def __post_init__(self) -> None:
        if not _is_canonical_code(self.presentation_version):
            raise ValueError("A versão do estado visual não é válida.")
        if (
            not isinstance(self.players, tuple)
            or not all(isinstance(player, PresentedPlayer) for player in self.players)
        ):
            raise ValueError("Os jogadores do estado visual não são válidos.")
        for side in MatchSide:
            if len(self.players_for(side)) != 11:
                raise ValueError("O estado visual deve conter 11 jogadores de cada lado.")
        identities = tuple((player.side, player.player_id) for player in self.players)
        if len(set(identities)) != len(identities):
            raise ValueError("As identidades dos jogadores visuais devem ser únicas.")
        if not isinstance(self.ball_position, NormalizedPoint):
            raise ValueError("A posição visual da bola não é válida.")
        if (self.ball_holder_side is None) != (self.ball_holder_id is None):
            raise ValueError("O portador visual da bola está incompleto.")
        if self.ball_holder_side is not None:
            if not isinstance(self.ball_holder_side, MatchSide) or not _is_positive_int(
                self.ball_holder_id
            ):
                raise ValueError("O portador visual da bola não é válido.")
            if self.ball_position != self.position_for(
                self.ball_holder_side, self.ball_holder_id
            ):
                raise ValueError("A bola deve coincidir com seu portador visual.")
        if self.last_event_sequence is not None and not _is_positive_int(
            self.last_event_sequence
        ):
            raise ValueError("A última sequência visualizada não é válida.")

    def players_for(self, side: MatchSide) -> tuple[PresentedPlayer, ...]:
        """Return the visual players for one match side in stable order."""

        return tuple(player for player in self.players if player.side is side)

    def position_for(self, side: MatchSide, player_id: int) -> NormalizedPoint:
        """Return one participant's exact position in the shared visual field."""

        try:
            return next(
                player.position
                for player in self.players
                if player.side is side and player.player_id == player_id
            )
        except StopIteration as error:
            raise ValueError("O jogador não existe no estado visual.") from error

    def to_snapshot(self) -> dict[str, object]:
        """Return a JSON-compatible visual checkpoint."""

        return {
            "presentation_version": self.presentation_version,
            "players": [
                {
                    "side": player.side.value,
                    "player_id": player.player_id,
                    "x": player.position.x,
                    "y": player.position.y,
                }
                for player in self.players
            ],
            "ball_position": {
                "x": self.ball_position.x,
                "y": self.ball_position.y,
            },
            "ball_holder_side": (
                self.ball_holder_side.value if self.ball_holder_side else None
            ),
            "ball_holder_id": self.ball_holder_id,
            "last_event_sequence": self.last_event_sequence,
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, object]) -> PresentationState:
        """Restore and validate a visual checkpoint."""

        if not isinstance(snapshot, Mapping):
            raise ValueError("O snapshot do estado visual não é válido.")
        try:
            players = snapshot["players"]
            ball_position = snapshot["ball_position"]
            holder_side = snapshot["ball_holder_side"]
            if not isinstance(players, list) or not isinstance(ball_position, Mapping):
                raise ValueError
            return cls(
                presentation_version=snapshot["presentation_version"],
                players=tuple(_player_from_snapshot(player) for player in players),
                ball_position=NormalizedPoint(
                    x=ball_position["x"],
                    y=ball_position["y"],
                ),
                ball_holder_side=(
                    MatchSide(holder_side) if holder_side is not None else None
                ),
                ball_holder_id=snapshot["ball_holder_id"],
                last_event_sequence=snapshot["last_event_sequence"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("O snapshot do estado visual não é válido.") from error


@dataclass(frozen=True, slots=True)
class SceneAdvance:
    """One visual scene together with its immutable state boundaries."""

    start_state: PresentationState
    scene: PresentationScene
    end_state: PresentationState

    def __post_init__(self) -> None:
        if not isinstance(self.start_state, PresentationState) or not isinstance(
            self.end_state, PresentationState
        ):
            raise ValueError("Os limites do avanço visual não são válidos.")
        if not isinstance(self.scene, PresentationScene):
            raise ValueError("A cena do avanço visual não é válida.")
        if self.scene.presentation_version != self.start_state.presentation_version:
            raise ValueError("A versão da cena não corresponde ao estado visual.")
        if self.end_state.last_event_sequence != self.scene.event_sequence:
            raise ValueError("O estado final não confirma a sequência da cena.")


def advance_pass_scene(
    state: PresentationState,
    event: MatchEvent,
) -> SceneAdvance:
    """Advance the visual ball holder through one confirmed pass event."""

    if not isinstance(state, PresentationState):
        raise ValueError("O estado visual do passe não é válido.")
    if not isinstance(event, MatchEvent):
        raise ValueError("O evento visual do passe não é válido.")
    if event.event_type is not MatchEventType.PASS or event.team_side is None:
        raise ValueError("O avanço de passe exige um evento de passe válido.")
    if len(event.participant_ids) != 2:
        raise ValueError("O avanço de passe exige exatamente dois participantes.")
    sender_id, receiver_id = event.participant_ids
    if (
        state.ball_holder_side is not event.team_side
        or state.ball_holder_id != sender_id
    ):
        raise ValueError("O autor do passe não possui a bola no estado visual atual.")
    if (
        state.last_event_sequence is not None
        and event.sequence != state.last_event_sequence + 1
    ):
        raise ValueError("A sequência dos eventos visuais deve avançar de um em um.")

    participant_positions = {
        sender_id: state.position_for(event.team_side, sender_id),
        receiver_id: state.position_for(event.team_side, receiver_id),
    }
    scene = build_pass_scene(
        event,
        participant_positions=participant_positions,
        presentation_version=state.presentation_version,
    )
    end_state = replace(
        state,
        ball_position=participant_positions[receiver_id],
        ball_holder_side=event.team_side,
        ball_holder_id=receiver_id,
        last_event_sequence=event.sequence,
    )
    return SceneAdvance(start_state=state, scene=scene, end_state=end_state)


def advance_carry_scene(
    state: PresentationState,
    event: MatchEvent,
    destination_position: NormalizedPoint,
) -> SceneAdvance:
    """Move the current visual ball holder and ball through a confirmed carry."""

    if not isinstance(state, PresentationState):
        raise ValueError("O estado visual da condução não é válido.")
    if not isinstance(event, MatchEvent):
        raise ValueError("O evento visual da condução não é válido.")
    if event.event_type is not MatchEventType.CARRY or event.team_side is None:
        raise ValueError("O avanço de condução exige um evento de condução válido.")
    if len(event.participant_ids) != 1:
        raise ValueError("O avanço de condução exige exatamente um participante.")
    if not isinstance(destination_position, NormalizedPoint):
        raise ValueError("O destino visual da condução não é válido.")
    player_id = event.participant_ids[0]
    if (
        state.ball_holder_side is not event.team_side
        or state.ball_holder_id != player_id
    ):
        raise ValueError("O autor da condução não possui a bola no estado visual atual.")
    if (
        state.last_event_sequence is not None
        and event.sequence != state.last_event_sequence + 1
    ):
        raise ValueError("A sequência dos eventos visuais deve avançar de um em um.")

    start_position = state.position_for(event.team_side, player_id)
    progress = _clamp(
        (destination_position.x - start_position.x) * CARRY_BLOCK_PROGRESS_RATIO,
        -MAX_CARRY_BLOCK_PROGRESS,
        MAX_CARRY_BLOCK_PROGRESS,
    )
    player_destinations = {
        (player.side, player.player_id): (
            destination_position
            if player.side is event.team_side and player.player_id == player_id
            else NormalizedPoint(
                x=_clamp(player.position.x + progress, 0, 100),
                y=_clamp(
                    player.position.y
                    + _clamp(
                        (destination_position.y - player.position.y)
                        * CARRY_BLOCK_LATERAL_RATIO,
                        -MAX_CARRY_BLOCK_LATERAL,
                        MAX_CARRY_BLOCK_LATERAL,
                    ),
                    0,
                    100,
                ),
            )
        )
        for player in state.players
    }
    carrier_identity = (event.team_side, player_id)
    player_movements = {
        carrier_identity: (start_position, destination_position),
        **{
            (player.side, player.player_id): (
                player.position,
                player_destinations[(player.side, player.player_id)],
            )
            for player in state.players
            if (player.side, player.player_id) != carrier_identity
        },
    }
    scene = build_carry_scene(
        event,
        start_position=start_position,
        destination_position=destination_position,
        player_movements=player_movements,
        presentation_version=state.presentation_version,
    )
    moved_players = tuple(
        replace(
            player,
            position=player_destinations[(player.side, player.player_id)],
        )
        for player in state.players
    )
    end_state = replace(
        state,
        players=moved_players,
        ball_position=destination_position,
        last_event_sequence=event.sequence,
    )
    return SceneAdvance(start_state=state, scene=scene, end_state=end_state)


def advance_shot_scene(
    state: PresentationState,
    event: MatchEvent,
    target_position: NormalizedPoint,
) -> SceneAdvance:
    """Move the ball toward a confirmed shot target and release its holder."""

    if not isinstance(state, PresentationState):
        raise ValueError("O estado visual da finalização não é válido.")
    if not isinstance(event, MatchEvent):
        raise ValueError("O evento visual da finalização não é válido.")
    if event.event_type is not MatchEventType.SHOT or event.team_side is None:
        raise ValueError("O avanço exige um evento de finalização válido.")
    if len(event.participant_ids) != 1:
        raise ValueError("O avanço de finalização exige exatamente um participante.")
    if not isinstance(target_position, NormalizedPoint):
        raise ValueError("O alvo visual da finalização não é válido.")
    player_id = event.participant_ids[0]
    if (
        state.ball_holder_side is not event.team_side
        or state.ball_holder_id != player_id
    ):
        raise ValueError("O autor da finalização não possui a bola no estado visual atual.")
    if (
        state.last_event_sequence is not None
        and event.sequence != state.last_event_sequence + 1
    ):
        raise ValueError("A sequência dos eventos visuais deve avançar de um em um.")

    scene = build_shot_scene(
        event,
        start_position=state.position_for(event.team_side, player_id),
        target_position=target_position,
        presentation_version=state.presentation_version,
    )
    end_state = replace(
        state,
        ball_position=target_position,
        ball_holder_side=None,
        ball_holder_id=None,
        last_event_sequence=event.sequence,
    )
    return SceneAdvance(start_state=state, scene=scene, end_state=end_state)


def _player_from_snapshot(snapshot: object) -> PresentedPlayer:
    if not isinstance(snapshot, Mapping):
        raise ValueError
    return PresentedPlayer(
        side=MatchSide(snapshot["side"]),
        player_id=snapshot["player_id"],
        position=NormalizedPoint(x=snapshot["x"], y=snapshot["y"]),
    )


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def _is_canonical_code(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value
