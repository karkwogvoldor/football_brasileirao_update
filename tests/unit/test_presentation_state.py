from dataclasses import FrozenInstanceError, replace

import pytest

from brafoot.engine.clock import MatchClock, MatchPeriod
from brafoot.engine.events import MatchEvent, MatchEventType
from brafoot.engine.matches import MatchSide
from brafoot.engine.zones import FieldLane, FieldThird, FieldZone
from brafoot.presentation.scenes import NormalizedPoint
from brafoot.presentation.state import (
    PresentationState,
    PresentedPlayer,
    advance_carry_scene,
    advance_pass_scene,
    advance_shot_scene,
)


HOME_POSITIONS = {
    1: (6, 50),
    2: (19, 17),
    3: (17, 39),
    4: (17, 61),
    6: (19, 83),
    5: (31, 27),
    8: (33, 50),
    10: (31, 73),
    7: (41, 20),
    9: (42, 50),
    11: (41, 80),
}


def make_players() -> tuple[PresentedPlayer, ...]:
    home = tuple(
        PresentedPlayer(MatchSide.HOME, player_id, NormalizedPoint(x, y))
        for player_id, (x, y) in HOME_POSITIONS.items()
    )
    away = tuple(
        PresentedPlayer(
            MatchSide.AWAY,
            player_id,
            NormalizedPoint(100 - x, 100 - y),
        )
        for player_id, (x, y) in HOME_POSITIONS.items()
    )
    return home + away


def make_state(**overrides) -> PresentationState:
    values = {
        "presentation_version": "2026.1",
        "players": make_players(),
        "ball_position": NormalizedPoint(*HOME_POSITIONS[8]),
        "ball_holder_side": MatchSide.HOME,
        "ball_holder_id": 8,
        "last_event_sequence": None,
    }
    values.update(overrides)
    return PresentationState(**values)


def make_pass(
    sequence: int,
    sender_id: int,
    receiver_id: int,
    *,
    side: MatchSide = MatchSide.HOME,
) -> MatchEvent:
    return MatchEvent(
        sequence=sequence,
        clock=MatchClock(120 + sequence, MatchPeriod.FIRST_HALF),
        event_type=MatchEventType.PASS,
        team_side=side,
        participant_ids=(sender_id, receiver_id),
        origin_zone=FieldZone(FieldThird.MIDDLE, FieldLane.CENTER),
        destination_zone=FieldZone(FieldThird.ATTACKING, FieldLane.CENTER),
        context="open_play",
        outcome="completed",
        explanation=f"Passe de {sender_id} para {receiver_id}.",
    )


def make_carry(
    sequence: int,
    player_id: int,
    *,
    side: MatchSide = MatchSide.HOME,
) -> MatchEvent:
    return MatchEvent(
        sequence=sequence,
        clock=MatchClock(120 + sequence, MatchPeriod.FIRST_HALF),
        event_type=MatchEventType.CARRY,
        team_side=side,
        participant_ids=(player_id,),
        origin_zone=FieldZone(FieldThird.MIDDLE, FieldLane.RIGHT),
        destination_zone=FieldZone(FieldThird.ATTACKING, FieldLane.RIGHT),
        context="open_play",
        outcome="progressed",
        explanation=f"Condução de {player_id}.",
    )


def make_shot(
    sequence: int,
    player_id: int,
    *,
    side: MatchSide = MatchSide.HOME,
) -> MatchEvent:
    return MatchEvent(
        sequence=sequence,
        clock=MatchClock(120 + sequence, MatchPeriod.FIRST_HALF),
        event_type=MatchEventType.SHOT,
        team_side=side,
        participant_ids=(player_id,),
        origin_zone=FieldZone(FieldThird.ATTACKING, FieldLane.RIGHT),
        destination_zone=FieldZone(FieldThird.ATTACKING, FieldLane.CENTER),
        context="open_play",
        outcome="on_target",
        explanation=f"Finalização de {player_id}.",
    )


# Mantém exatamente onze posições distintas para cada lado da apresentação.
def test_presentation_state_requires_complete_two_team_shape():
    state = make_state()

    assert len(state.players) == 22
    assert len(state.players_for(MatchSide.HOME)) == 11
    assert len(state.players_for(MatchSide.AWAY)) == 11
    assert state.position_for(MatchSide.HOME, 8) == NormalizedPoint(33, 50)
    assert state.position_for(MatchSide.AWAY, 8) == NormalizedPoint(67, 50)


# Persiste e restaura o estado visual sem perder a identidade composta dos jogadores.
def test_presentation_state_snapshot_round_trip_is_lossless():
    state = make_state()

    assert PresentationState.from_snapshot(state.to_snapshot()) == state


# Mantém o estado visual imutável depois que uma cena começa a ser reproduzida.
def test_presentation_state_is_immutable():
    state = make_state()

    with pytest.raises(FrozenInstanceError):
        state.ball_holder_id = 9


# Faz a bola partir do passador e encerra o avanço com o receptor em posse visual.
def test_pass_advance_returns_scene_and_new_visual_state():
    state = make_state()

    advance = advance_pass_scene(state, make_pass(1, 8, 9))

    assert advance.start_state is state
    assert advance.scene.keyframes[0].position == state.position_for(
        MatchSide.HOME, 8
    )
    assert len(advance.scene.player_tracks) == 22
    assert advance.scene.keyframes[-1].position == advance.end_state.position_for(
        MatchSide.HOME, 9
    )
    assert advance.end_state.ball_position == NormalizedPoint(46.5, 50)
    assert advance.end_state.ball_holder_side is MatchSide.HOME
    assert advance.end_state.ball_holder_id == 9
    assert advance.end_state.last_event_sequence == 1
    assert state.ball_holder_id == 8
    for track in advance.scene.player_tracks:
        assert track.keyframes[0].position == state.position_for(
            track.side, track.player_id
        )
        assert track.keyframes[-1].position == advance.end_state.position_for(
            track.side, track.player_id
        )


# Encadeia passes usando o fim de uma cena como início exato da seguinte.
def test_pass_advances_chain_without_ball_teleportation():
    first = advance_pass_scene(make_state(), make_pass(1, 8, 9))
    second = advance_pass_scene(first.end_state, make_pass(2, 9, 7))
    third = advance_pass_scene(second.end_state, make_pass(3, 7, 10))

    assert first.scene.keyframes[-1].position == second.scene.keyframes[0].position
    assert second.scene.keyframes[-1].position == third.scene.keyframes[0].position
    assert third.end_state.ball_holder_id == 10
    assert third.end_state.ball_position == third.end_state.position_for(
        MatchSide.HOME, 10
    )
    assert third.end_state.ball_position == NormalizedPoint(30, 67)


# Move o portador, a bola e os dois blocos para posições finais consistentes.
def test_carry_advance_updates_collective_shape_and_ball_together():
    state = make_state()
    destination = NormalizedPoint(45, 55)

    advance = advance_carry_scene(state, make_carry(1, 8), destination)

    assert advance.scene.keyframes[0].position == NormalizedPoint(33, 50)
    assert advance.scene.keyframes[-1].position == destination
    assert len(advance.scene.player_tracks) == 22
    assert advance.end_state.position_for(MatchSide.HOME, 8) == destination
    assert advance.end_state.position_for(MatchSide.HOME, 10) == NormalizedPoint(
        37, 70.3
    )
    assert advance.end_state.position_for(MatchSide.AWAY, 8) == NormalizedPoint(
        73, 50.75
    )
    assert advance.end_state.ball_position == destination
    assert advance.end_state.ball_holder_id == 8
    assert advance.end_state.last_event_sequence == 1
    assert state.position_for(MatchSide.HOME, 8) == NormalizedPoint(33, 50)
    for track in advance.scene.player_tracks:
        assert track.keyframes[0].position == state.position_for(
            track.side, track.player_id
        )
        assert track.keyframes[-1].position == advance.end_state.position_for(
            track.side, track.player_id
        )


# Faz o passe posterior começar exatamente no destino final da condução.
def test_carry_then_pass_chain_starts_from_updated_player_position():
    carry = advance_carry_scene(
        make_state(),
        make_carry(1, 8),
        NormalizedPoint(45, 55),
    )

    following_pass = advance_pass_scene(carry.end_state, make_pass(2, 8, 9))

    assert carry.scene.keyframes[-1].position == following_pass.scene.keyframes[0].position
    assert following_pass.end_state.ball_holder_id == 9


# Rejeita condução solicitada por jogador que não possui a bola.
def test_carry_advance_requires_current_ball_holder():
    with pytest.raises(ValueError, match="possui a bola"):
        advance_carry_scene(
            make_state(),
            make_carry(1, 10),
            NormalizedPoint(43, 68),
        )


# Leva a bola ao alvo e encerra a posse visual sem mover os jogadores.
def test_shot_advance_moves_ball_to_target_and_releases_holder():
    start = NormalizedPoint(*HOME_POSITIONS[11])
    state = make_state(
        ball_position=start,
        ball_holder_side=MatchSide.HOME,
        ball_holder_id=11,
        last_event_sequence=5,
    )
    target = NormalizedPoint(98, 55)

    advance = advance_shot_scene(state, make_shot(6, 11), target)

    assert advance.scene.keyframes[0].position == start
    assert advance.scene.keyframes[-1].position == target
    assert len(advance.scene.player_tracks) == 22
    assert advance.end_state.position_for(MatchSide.HOME, 11) == NormalizedPoint(
        47, 77
    )
    assert advance.end_state.players != state.players
    assert advance.end_state.ball_position == target
    assert advance.end_state.ball_holder_side is None
    assert advance.end_state.ball_holder_id is None
    assert advance.end_state.last_event_sequence == 6
    assert state.ball_holder_id == 11
    for track in advance.scene.player_tracks:
        assert track.keyframes[0].position == state.position_for(
            track.side, track.player_id
        )
        assert track.keyframes[-1].position == advance.end_state.position_for(
            track.side, track.player_id
        )


# Rejeita finalização solicitada por jogador que não possui a bola.
def test_shot_advance_requires_current_ball_holder():
    with pytest.raises(ValueError, match="possui a bola"):
        advance_shot_scene(
            make_state(),
            make_shot(1, 11),
            NormalizedPoint(98, 55),
        )


# Rejeita um passe cujo autor não possui a bola no estado visual atual.
def test_pass_advance_requires_current_ball_holder_as_sender():
    with pytest.raises(ValueError, match="possui a bola"):
        advance_pass_scene(make_state(), make_pass(1, 9, 7))


# Rejeita outros tipos de evento na operação específica de avanço de passe.
def test_pass_advance_rejects_non_pass_event():
    event = replace(make_pass(1, 8, 9), event_type=MatchEventType.CARRY)

    with pytest.raises(ValueError, match="evento de passe"):
        advance_pass_scene(make_state(), event)


# Rejeita lacunas na sequência visual para preservar a ordem dos eventos confirmados.
def test_pass_advance_requires_contiguous_event_sequence():
    state = make_state(last_event_sequence=3)

    with pytest.raises(ValueError, match="sequência"):
        advance_pass_scene(state, make_pass(5, 8, 9))


# Rejeita estados incompletos que não representem onze jogadores de cada lado.
def test_presentation_state_rejects_incomplete_formation():
    with pytest.raises(ValueError, match="11 jogadores"):
        make_state(players=make_players()[:-1])
