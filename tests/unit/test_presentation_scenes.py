from dataclasses import FrozenInstanceError

import pytest

from brafoot.engine.clock import MatchClock, MatchPeriod
from brafoot.engine.events import MatchEvent, MatchEventType
from brafoot.engine.matches import MatchSide
from brafoot.engine.zones import FieldLane, FieldThird, FieldZone
from brafoot.presentation.scenes import (
    DEFAULT_PRESENTATION_VERSION,
    NormalizedPoint,
    PresentationScene,
    build_pass_scene,
)


def make_pass_event(**overrides) -> MatchEvent:
    values = {
        "sequence": 7,
        "clock": MatchClock(125, MatchPeriod.FIRST_HALF),
        "event_type": MatchEventType.PASS,
        "team_side": MatchSide.HOME,
        "participant_ids": (8, 9),
        "origin_zone": FieldZone(FieldThird.MIDDLE, FieldLane.CENTER),
        "destination_zone": FieldZone(FieldThird.ATTACKING, FieldLane.LEFT),
        "context": "open_play",
        "outcome": "completed",
        "explanation": "O passe avançou da faixa central para o ataque.",
    }
    values.update(overrides)
    return MatchEvent(**values)


def make_participant_positions(
    side: MatchSide = MatchSide.HOME,
) -> dict[int, NormalizedPoint]:
    home_positions = {
        8: NormalizedPoint(33, 50),
        9: NormalizedPoint(42, 20),
    }
    if side is MatchSide.HOME:
        return home_positions
    return {
        player_id: NormalizedPoint(100 - point.x, 100 - point.y)
        for player_id, point in home_positions.items()
    }


def build_scene(event: MatchEvent) -> PresentationScene:
    return build_pass_scene(
        event,
        participant_positions=make_participant_positions(event.team_side),
    )


# Converte um passe sem alterar o evento esportivo que originou a cena.
def test_pass_scene_preserves_source_event_and_presentation_metadata():
    event = make_pass_event()

    scene = build_scene(event)

    assert scene.presentation_version == DEFAULT_PRESENTATION_VERSION
    assert scene.event_sequence == 7
    assert scene.event_type is MatchEventType.PASS
    assert scene.team_side is MatchSide.HOME
    assert scene.participant_ids == (8, 9)
    assert scene.duration_ms == 1200
    assert scene.narration == event.explanation
    assert event.origin_zone == FieldZone(FieldThird.MIDDLE, FieldLane.CENTER)


# Inicia a bola exatamente em A e encerra exatamente em B, não no centro das zonas.
def test_pass_scene_connects_exact_participant_positions():
    event = make_pass_event()
    positions = make_participant_positions()

    scene = build_pass_scene(event, participant_positions=positions)

    assert scene.keyframes[0].position == positions[8]
    assert scene.keyframes[-1].position == positions[9]


# Mantém o keyframe intermediário na reta entre passador e receptor.
def test_pass_scene_uses_straight_line_trajectory():
    scene = build_scene(make_pass_event())
    start, midpoint, end = (frame.position for frame in scene.keyframes)

    assert midpoint.x == (start.x + end.x) / 2
    assert midpoint.y == (start.y + end.y) / 2


# Produz exatamente os mesmos keyframes para o mesmo evento e versão visual.
def test_pass_scene_is_deterministic_for_same_event():
    event = make_pass_event()

    assert build_scene(event) == build_scene(event)


# Espelha no campo absoluto as zonas relativas de um passe do visitante.
def test_away_pass_scene_mirrors_home_coordinates():
    home_scene = build_scene(make_pass_event())
    away_scene = build_scene(make_pass_event(team_side=MatchSide.AWAY))

    for home_frame, away_frame in zip(home_scene.keyframes, away_scene.keyframes):
        assert away_frame.at_ms == home_frame.at_ms
        assert away_frame.position.x == 100 - home_frame.position.x
        assert away_frame.position.y == 100 - home_frame.position.y


# Mantém todos os keyframes derivados dos participantes em coordenadas normalizadas.
def test_pass_scene_keeps_keyframes_in_normalized_bounds():
    scene = build_scene(make_pass_event())

    assert all(0 <= frame.position.x <= 100 for frame in scene.keyframes)
    assert all(0 <= frame.position.y <= 100 for frame in scene.keyframes)


# Rejeita eventos que não descrevem um passe completo entre dois participantes.
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"event_type": MatchEventType.CARRY}, "passe"),
        ({"participant_ids": (8,)}, "dois participantes"),
        ({"origin_zone": None}, "zonas"),
        ({"destination_zone": None}, "zonas"),
    ],
)
def test_pass_scene_requires_complete_pass_event(overrides, message):
    with pytest.raises(ValueError, match=message):
        event = make_pass_event(**overrides)
        build_pass_scene(
            event,
            participant_positions=make_participant_positions(event.team_side),
        )


# Rejeita cenas sem a posição exata de qualquer participante do passe.
def test_pass_scene_requires_both_participant_positions():
    with pytest.raises(ValueError, match="posições dos participantes"):
        build_pass_scene(
            make_pass_event(),
            participant_positions={8: NormalizedPoint(33, 50)},
        )


# Persiste, restaura e mantém a cena confirmada imutável.
def test_presentation_scene_snapshot_round_trip_is_lossless_and_immutable():
    scene = build_scene(make_pass_event())

    assert PresentationScene.from_snapshot(scene.to_snapshot()) == scene
    with pytest.raises(FrozenInstanceError):
        scene.duration_ms = 800
