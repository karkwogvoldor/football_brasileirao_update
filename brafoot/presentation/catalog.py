"""Versioned development scenarios for reviewing presentation choreography."""

from __future__ import annotations

from dataclasses import replace

from brafoot.engine.clock import MatchClock, MatchPeriod
from brafoot.engine.events import MatchEvent, MatchEventType
from brafoot.engine.matches import MatchSide
from brafoot.engine.zones import FieldLane, FieldThird, FieldZone
from brafoot.presentation.scenes import (
    DEFAULT_PRESENTATION_VERSION,
    NormalizedPoint,
    PlayerTrack,
    PresentationScene,
    SceneKeyframe,
)
from brafoot.presentation.state import (
    INTERLOCKING_BLOCKS,
    PresentationState,
    PresentedPlayer,
    SceneAdvance,
    advance_carry_scene,
    advance_pass_scene,
    advance_shot_scene,
)

CATALOG_VERSION = "2026.1"

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


# Formação compacta: as linhas dos dois times ficam próximas, para que avancem e recuem
# encaixadas (espelhadas) em vez de isoladas, com a zaga mais alta que a entrada da área.
INTERLOCKED_HOME_POSITIONS = {
    1: (7, 50),
    2: (26, 17),
    3: (24, 39),
    4: (24, 61),
    6: (26, 83),
    5: (36, 27),
    8: (38, 50),
    10: (36, 73),
    7: (48, 20),
    9: (50, 50),
    11: (48, 80),
}


def build_demo_sequence_snapshot() -> dict[str, object]:
    """Return the main deterministic presentation sequence used by /partida."""

    state = _initial_state(holder_id=8, formation=INTERLOCKED_HOME_POSITIONS)
    initial_state = state
    scenes = []
    passes = (
        (8, 9, "O camisa 8 encontra o centroavante."),
        (9, 7, "O centroavante abre a jogada para a ponta."),
        (7, 10, "O ponta devolve a bola ao meio-campista."),
    )
    for sequence, (sender_id, receiver_id, explanation) in enumerate(
        passes, start=1
    ):
        advance = advance_pass_scene(
            state,
            _event(
                sequence,
                MatchEventType.PASS,
                (sender_id, receiver_id),
                explanation,
            ),
            shape=INTERLOCKING_BLOCKS,
        )
        scenes.append(advance.scene.to_snapshot())
        state = advance.end_state

    carry = advance_carry_scene(
        state,
        _event(
            4,
            MatchEventType.CARRY,
            (10,),
            "O meio-campista conduz a bola antes do passe final.",
            lane=FieldLane.RIGHT,
            outcome="progressed",
        ),
        NormalizedPoint(42, 70),
        shape=INTERLOCKING_BLOCKS,
    )
    scenes.append(carry.scene.to_snapshot())
    state = carry.end_state

    final_pass = advance_pass_scene(
        state,
        _event(
            5,
            MatchEventType.PASS,
            (10, 11),
            "Após conduzir, o meio-campista encontra o ponta.",
            lane=FieldLane.RIGHT,
        ),
        shape=INTERLOCKING_BLOCKS,
    )
    scenes.append(final_pass.scene.to_snapshot())
    state = final_pass.end_state

    shot = advance_shot_scene(
        state,
        _event(
            6,
            MatchEventType.SHOT,
            (11,),
            "O ponta domina e finaliza em direção ao gol.",
            lane=FieldLane.RIGHT,
            outcome="on_target",
        ),
        NormalizedPoint(98, 55),
        shape=INTERLOCKING_BLOCKS,
    )
    scenes.append(shot.scene.to_snapshot())
    state = shot.end_state

    return {
        "presentation_version": initial_state.presentation_version,
        "initial_state": initial_state.to_snapshot(),
        "scenes": scenes,
        "final_state": state.to_snapshot(),
    }


def build_developer_scene_catalog() -> dict[str, object]:
    """Return deterministic review scenarios grouped by visual purpose."""

    scenarios = [
        _pass_scenario(
            "pass-short-center",
            "Passe curto central",
            "Circulação curta com deslocamento simultâneo dos dois blocos.",
            8,
            9,
        ),
        _pass_scenario(
            "pass-diagonal-left",
            "Passe diagonal para a ponta",
            "Mudança diagonal do centro para o corredor esquerdo.",
            8,
            7,
        ),
        _carry_scenario(),
        _shot_scenario(),
        _switch_of_play_scenario(),
        _goalkeeper_adjustment_scenario(),
        _interception_attempt_scenario(),
        {
            "id": "composite-attacking-sequence",
            "version": 2,
            "category": "composite",
            "title": "Ataque completo",
            "description": "Passes, condução e finalização encadeados sem teletransporte.",
            "focus": "composition",
            "ball_visible": True,
            "status": "pending",
            **build_demo_sequence_snapshot(),
        },
    ]
    return {
        "catalog_version": CATALOG_VERSION,
        "presentation_version": DEFAULT_PRESENTATION_VERSION,
        "groups": [
            {"id": "ball", "title": "Ações com bola"},
            {"id": "movement", "title": "Movimentos sem bola"},
            {"id": "composite", "title": "Cenários compostos"},
        ],
        "scenarios": scenarios,
    }


def _pass_scenario(
    scenario_id: str,
    title: str,
    description: str,
    sender_id: int,
    receiver_id: int,
) -> dict[str, object]:
    state = _initial_state(holder_id=sender_id)
    advance = advance_pass_scene(
        state,
        _event(
            1,
            MatchEventType.PASS,
            (sender_id, receiver_id),
            description,
        ),
    )
    return _scenario_snapshot(
        scenario_id,
        title,
        description,
        "ball",
        "ball",
        state,
        (advance,),
    )


def _carry_scenario() -> dict[str, object]:
    state = _initial_state(holder_id=10)
    description = "Condução pelo corredor direito com acompanhamento dos dois blocos."
    advance = advance_carry_scene(
        state,
        _event(
            1,
            MatchEventType.CARRY,
            (10,),
            description,
            lane=FieldLane.RIGHT,
            outcome="progressed",
        ),
        NormalizedPoint(42, 71),
        supporting_destinations={
            # Ponta esquerda abre o campo e oferece linha de passe.
            (MatchSide.HOME, 7): NormalizedPoint(49, 12),
            # Centroavante ataca o espaço entre os zagueiros adversários.
            (MatchSide.HOME, 9): NormalizedPoint(52, 50),
            # Ponta direita repete a abertura do ponta esquerda, pelo lado oposto.
            (MatchSide.HOME, 11): NormalizedPoint(49, 88),
        },
    )
    return _scenario_snapshot(
        "carry-right-channel",
        "Condução pelo corredor",
        description,
        "ball",
        "ball",
        state,
        (advance,),
        version=3,
    )


def _shot_scenario() -> dict[str, object]:
    state = _initial_state(holder_id=11, home_overrides={11: (76, 72)})
    description = "Finalização próxima à área para revisar velocidade e direção da bola."
    advance = advance_shot_scene(
        state,
        _event(
            1,
            MatchEventType.SHOT,
            (11,),
            description,
            lane=FieldLane.RIGHT,
            outcome="on_target",
        ),
        NormalizedPoint(98, 54),
    )
    return _scenario_snapshot(
        "shot-near-area",
        "Finalização próxima",
        description,
        "ball",
        "ball",
        state,
        (advance,),
        version=2,
    )


def _switch_of_play_scenario() -> dict[str, object]:
    """Inversão de jogo: do lateral direito ao esquerdo, com o bloco pendendo para a direita."""

    def shifted_right(y: float) -> float:
        # Os dois times se comprimem em torno do lado da bola (direita, y alto).
        return min(95.0, 50 + (y - 50) * 0.6 + 14)

    home = {
        player_id: (x, shifted_right(y))
        for player_id, (x, y) in HOME_POSITIONS.items()
    }
    # Laterais bem abertos: o direito tem a bola, o esquerdo está livre do outro lado.
    home[6] = (30, 92)
    home[2] = (30, 8)
    away = {
        player_id: (100 - x, shifted_right(100 - y))
        for player_id, (x, y) in HOME_POSITIONS.items()
    }
    state = _initial_state(holder_id=6, formation=home, away_positions=away)
    description = (
        "O lateral direito lança para o lateral esquerdo, aberto do outro lado, "
        "e o bloco que estava deslocado para a direita passa a jogar pela esquerda."
    )
    event = replace(
        _event(1, MatchEventType.PASS, (6, 2), description),
        origin_zone=FieldZone(FieldThird.MIDDLE, FieldLane.RIGHT),
        destination_zone=FieldZone(FieldThird.MIDDLE, FieldLane.LEFT),
    )
    advance = advance_pass_scene(
        state,
        event,
        lateral_ratio=0.45,
        max_lateral=18,
    )
    return _scenario_snapshot(
        "movement-switch-of-play",
        "Inversão de jogo",
        description,
        "movement",
        "players",
        state,
        (advance,),
    )


def _goalkeeper_adjustment_scenario() -> dict[str, object]:
    state = _initial_state(holder_id=8)
    start = state.position_for(MatchSide.AWAY, 1)
    end = NormalizedPoint(96, 54)
    duration = 1200
    ball_frames = _stationary_frames(state.ball_position, duration)
    goalkeeper_frames = (
        SceneKeyframe(0, start),
        SceneKeyframe(250, start),
        SceneKeyframe(900, end),
        SceneKeyframe(duration, end),
    )
    scene = PresentationScene(
        presentation_version=DEFAULT_PRESENTATION_VERSION,
        event_sequence=1,
        event_type=MatchEventType.CARRY,
        team_side=MatchSide.HOME,
        participant_ids=(8,),
        duration_ms=duration,
        keyframes=ball_frames,
        player_tracks=(PlayerTrack(MatchSide.AWAY, 1, goalkeeper_frames),),
        narration="O goleiro ajusta a posição com atraso em relação à circulação.",
    )
    end_state = _replace_player_position(state, MatchSide.AWAY, 1, end, sequence=1)
    return _scenario_snapshot_from_scenes(
        "movement-goalkeeper-adjustment",
        "Ajuste do goleiro",
        "Reação atrasada do goleiro a uma bola posicionada no meio-campo.",
        "movement",
        "players",
        state,
        (scene,),
        end_state,
        ball_visible=False,
    )


def _interception_attempt_scenario() -> dict[str, object]:
    state = _initial_state(holder_id=8)
    defender_start = state.position_for(MatchSide.AWAY, 3)
    defender_end = NormalizedPoint(62, 52)
    ball_end = NormalizedPoint(64, 50)
    duration = 1200
    scene = PresentationScene(
        presentation_version=DEFAULT_PRESENTATION_VERSION,
        event_sequence=1,
        event_type=MatchEventType.DUEL,
        team_side=MatchSide.HOME,
        participant_ids=(8, 3),
        duration_ms=duration,
        keyframes=(
            SceneKeyframe(0, state.ball_position),
            SceneKeyframe(600, NormalizedPoint(48.5, 50)),
            SceneKeyframe(duration, ball_end),
        ),
        player_tracks=(
            PlayerTrack(
                MatchSide.AWAY,
                3,
                (
                    SceneKeyframe(0, defender_start),
                    SceneKeyframe(180, defender_start),
                    SceneKeyframe(900, defender_end),
                    SceneKeyframe(duration, defender_end),
                ),
            ),
        ),
        narration="O defensor reage depois do passe e fecha a linha da bola.",
    )
    moved = _replace_player_position(
        state,
        MatchSide.AWAY,
        3,
        defender_end,
        sequence=1,
    )
    end_state = replace(
        moved,
        ball_position=ball_end,
        ball_holder_side=None,
        ball_holder_id=None,
    )
    return _scenario_snapshot_from_scenes(
        "movement-interception-attempt",
        "Tentativa de interceptação",
        "Defensor inicia com atraso e ataca a linha do passe sem decidir a posse.",
        "movement",
        "players",
        state,
        (scene,),
        end_state,
    )


def _scenario_snapshot(
    scenario_id: str,
    title: str,
    description: str,
    category: str,
    focus: str,
    initial_state: PresentationState,
    advances: tuple[SceneAdvance, ...],
    *,
    ball_visible: bool = True,
    version: int = 1,
) -> dict[str, object]:
    return _scenario_snapshot_from_scenes(
        scenario_id,
        title,
        description,
        category,
        focus,
        initial_state,
        tuple(advance.scene for advance in advances),
        advances[-1].end_state,
        ball_visible=ball_visible,
        version=version,
    )


def _scenario_snapshot_from_scenes(
    scenario_id: str,
    title: str,
    description: str,
    category: str,
    focus: str,
    initial_state: PresentationState,
    scenes: tuple[PresentationScene, ...],
    final_state: PresentationState,
    *,
    ball_visible: bool = True,
    version: int = 1,
) -> dict[str, object]:
    return {
        "id": scenario_id,
        "version": version,
        "category": category,
        "title": title,
        "description": description,
        "focus": focus,
        "ball_visible": ball_visible,
        "status": "pending",
        "presentation_version": initial_state.presentation_version,
        "initial_state": initial_state.to_snapshot(),
        "scenes": [scene.to_snapshot() for scene in scenes],
        "final_state": final_state.to_snapshot(),
    }


def _initial_state(
    *,
    holder_id: int,
    formation: dict[int, tuple[float, float]] | None = None,
    home_overrides: dict[int, tuple[float, float]] | None = None,
    away_positions: dict[int, tuple[float, float]] | None = None,
) -> PresentationState:
    """Monta o estado inicial: ``formation`` vale para os dois times (o visitante é
    espelhado) e ``home_overrides`` reposiciona apenas jogadores do time da casa e
    ``away_positions`` informa o visitante em coordenadas absolutas."""

    base = dict(formation or HOME_POSITIONS)
    home_positions = {**base, **(home_overrides or {})}
    home_players = tuple(
        PresentedPlayer(MatchSide.HOME, player_id, NormalizedPoint(x, y))
        for player_id, (x, y) in home_positions.items()
    )
    if away_positions is None:
        away_positions = {
            player_id: (100 - x, 100 - y) for player_id, (x, y) in base.items()
        }
    away_players = tuple(
        PresentedPlayer(MatchSide.AWAY, player_id, NormalizedPoint(x, y))
        for player_id, (x, y) in away_positions.items()
    )
    return PresentationState(
        presentation_version=DEFAULT_PRESENTATION_VERSION,
        players=home_players + away_players,
        ball_position=NormalizedPoint(*home_positions[holder_id]),
        ball_holder_side=MatchSide.HOME,
        ball_holder_id=holder_id,
        last_event_sequence=None,
    )


def _event(
    sequence: int,
    event_type: MatchEventType,
    participant_ids: tuple[int, ...],
    explanation: str,
    *,
    lane: FieldLane = FieldLane.CENTER,
    outcome: str = "completed",
) -> MatchEvent:
    return MatchEvent(
        sequence=sequence,
        clock=MatchClock(124 + sequence, MatchPeriod.FIRST_HALF),
        event_type=event_type,
        team_side=MatchSide.HOME,
        participant_ids=participant_ids,
        origin_zone=FieldZone(FieldThird.MIDDLE, lane),
        destination_zone=FieldZone(FieldThird.ATTACKING, lane),
        context="open_play",
        outcome=outcome,
        explanation=explanation,
    )


def _stationary_frames(
    position: NormalizedPoint,
    duration_ms: int,
) -> tuple[SceneKeyframe, ...]:
    return (
        SceneKeyframe(0, position),
        SceneKeyframe(duration_ms // 2, position),
        SceneKeyframe(duration_ms, position),
    )


def _replace_player_position(
    state: PresentationState,
    side: MatchSide,
    player_id: int,
    position: NormalizedPoint,
    *,
    sequence: int,
) -> PresentationState:
    players = tuple(
        replace(player, position=position)
        if player.side is side and player.player_id == player_id
        else player
        for player in state.players
    )
    return replace(state, players=players, last_event_sequence=sequence)
