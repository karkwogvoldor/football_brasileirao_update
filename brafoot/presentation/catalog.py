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
    CollectiveShape,
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
        _cross_far_post_scenario(),
        _offside_trap_scenario(),
        _offside_trap_success_scenario(),
        _overlap_fullback_scenario(),
        _counter_attack_scenario(),
        _high_press_scenario(),
        _short_goal_kick_scenario(),
        _one_two_scenario(),
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
    home[1] = (6, 54)
    # Laterais bem abertos: o direito tem a bola, o esquerdo está livre do outro lado.
    home[6] = (30, 92)
    home[2] = (30, 8)
    away = {
        player_id: (100 - x, shifted_right(100 - y))
        for player_id, (x, y) in HOME_POSITIONS.items()
    }
    away[1] = (94, 54)
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
        shape=CollectiveShape(
            forward_only=True,
            defending_retreat_ratio=0.5,
            defender_line_ratio=0.5,
            base_advance=3,
        ),
        # Depois de bater na bola, o lateral dá uma breve acompanhada para a frente.
        supporting_destinations={
            (MatchSide.HOME, 6): NormalizedPoint(38, 86),
            (MatchSide.HOME, 1): NormalizedPoint(6, 50),
            (MatchSide.AWAY, 1): NormalizedPoint(94, 50),
        },
        # Movimento mais lento e suave: o lançamento longo leva mais tempo.
        duration_ms=2600,
    )
    return _scenario_snapshot(
        "movement-switch-of-play",
        "Inversão de jogo",
        description,
        "movement",
        "players",
        state,
        (advance,),
        version=2,
    )


# Cenas baseadas em princípios táticos descritos em fontes de treinamento (ver
# docs/FONTES_CENAS.md). Coordenadas em % do campo: x vai do gol da casa (0) ao do
# visitante (100); y de 0 a 100 na largura. Gol: y 45–55; área: x>=84, y 20–80.


def _fixed(
    side: MatchSide, positions: dict[int, tuple[float, float]]
) -> dict[tuple[MatchSide, int], NormalizedPoint]:
    return {
        (side, player_id): NormalizedPoint(x, y)
        for player_id, (x, y) in positions.items()
    }


def _cross_far_post_scenario() -> dict[str, object]:
    """Cruzamento da direita: um atacante puxa o goleiro no primeiro pau, outro
    ataca o segundo pau e recebe, e um terceiro chega à meia-lua."""

    home = {
        1: (6, 50),
        2: (50, 18), 3: (52, 40), 4: (52, 60), 6: (50, 82),
        5: (66, 28), 8: (72, 50), 10: (66, 72),
        7: (82, 24), 9: (80, 50), 11: (78, 90),
    }
    away = {
        1: (94, 50),
        2: (88, 66), 3: (88, 56), 4: (88, 44), 6: (88, 34),
        5: (74, 70), 8: (74, 50), 10: (74, 30),
        7: (60, 68), 9: (58, 50), 11: (60, 32),
    }
    state = _initial_state(holder_id=11, formation=home, away_positions=away)
    description = (
        "A ponta direita cruza: o centroavante ataca o primeiro pau e leva a zaga, "
        "o ponta esquerda surge no segundo pau para finalizar e o meia chega à meia-lua."
    )
    event = replace(
        _event(1, MatchEventType.CROSS, (11, 7), description, lane=FieldLane.RIGHT),
        origin_zone=FieldZone(FieldThird.ATTACKING, FieldLane.RIGHT),
        destination_zone=FieldZone(FieldThird.ATTACKING, FieldLane.LEFT),
    )
    advance = advance_pass_scene(
        state,
        event,
        shape=CollectiveShape(
            forward_only=True,
            defending_retreat_ratio=0.3,
            defender_line_ratio=0.5,
            defender_min_x=8,
        ),
        supporting_destinations={
            **_fixed(
                MatchSide.HOME,
                {
                    1: (6, 50),
                    11: (83, 91),   # cruzador acompanha o lance
                    7: (92, 44),    # segundo pau: recebe o cruzamento
                    9: (94, 57),    # primeiro pau: puxa o goleiro e a marcação
                    8: (87, 52),    # ponto penal / bola viva
                    10: (82, 66),   # entrada da área, lado do cruzamento
                    5: (80, 30),    # entrada da área, lado oposto
                },
            ),
            **_fixed(
                MatchSide.AWAY,
                {
                    1: (95, 49),
                    2: (91, 62), 3: (91, 54), 4: (91, 46), 6: (91, 38),
                },
            ),
        },
        duration_ms=2200,
    )
    return _scenario_snapshot(
        "ball-cross-far-post",
        "Cruzamento para o segundo pau",
        description,
        "ball",
        "ball",
        state,
        (advance,),
    )


def _hold_all(
    state: PresentationState,
    *,
    except_ids: set[tuple[MatchSide, int]] | None = None,
) -> dict[tuple[MatchSide, int], NormalizedPoint]:
    """Mantém parados todos os jogadores do estado, menos os listados em ``except_ids``."""

    skip = except_ids or set()
    return {
        (player.side, player.player_id): player.position
        for player in state.players
        if (player.side, player.player_id) not in skip
    }


def _offside_trap_scenario() -> dict[str, object]:
    """Linha de impedimento ineficiente: a zaga sobe tarde. No momento do passe o
    centroavante ainda está na linha, portanto em condição legal, e escapa livre."""

    home = {
        1: (6, 50),
        2: (40, 18), 3: (40, 40), 4: (40, 60), 6: (40, 82),
        5: (56, 28), 8: (58, 50), 10: (56, 72),
        7: (66, 20), 9: (77, 50), 11: (66, 80),
    }
    away = {
        1: (92, 50),
        2: (78, 82), 3: (78, 60), 4: (78, 40), 6: (78, 18),
        5: (66, 72), 8: (66, 50), 10: (66, 28),
        7: (54, 66), 9: (54, 50), 11: (54, 34),
    }
    state = _initial_state(holder_id=8, formation=home, away_positions=away)
    description = (
        "A zaga visitante sobe tarde: no momento do passe o centroavante ainda está na "
        "linha, em condição legal, escapa nas suas costas e fica livre."
    )
    event = _event(1, MatchEventType.PASS, (8, 9), description)
    advance = advance_pass_scene(
        state,
        event,
        shape=INTERLOCKING_BLOCKS,
        supporting_destinations={
            **_fixed(
                MatchSide.HOME,
                {
                    1: (6, 50),
                    9: (84, 50),   # parte no momento do passe e recebe além da linha
                    7: (67, 20),
                    11: (67, 80),
                },
            ),
            **_fixed(
                MatchSide.AWAY,
                {
                    1: (89, 50),
                    2: (72, 82), 3: (72, 60), 4: (72, 40), 6: (72, 18),
                    5: (63, 72), 8: (63, 50), 10: (63, 28),
                    7: (53, 66), 9: (53, 50), 11: (53, 34),
                },
            ),
        },
        duration_ms=1600,
    )
    return _scenario_snapshot(
        "movement-offside-trap",
        "Linha de impedimento ineficiente",
        description,
        "movement",
        "players",
        state,
        (advance,),
        version=2,
    )


def _offside_trap_success_scenario() -> dict[str, object]:
    """Linha de impedimento bem-sucedida: a zaga sobe junta antes do passe e, no
    momento em que a bola é tocada, o centroavante já está além da linha."""

    home = {
        1: (6, 50),
        2: (40, 18), 3: (40, 40), 4: (40, 60), 6: (40, 82),
        5: (56, 28), 8: (58, 50), 10: (56, 72),
        7: (66, 20), 9: (74, 50), 11: (66, 80),
    }
    away = {
        1: (92, 50),
        2: (78, 82), 3: (78, 60), 4: (78, 40), 6: (78, 18),
        5: (66, 72), 8: (66, 50), 10: (66, 28),
        7: (54, 66), 9: (54, 50), 11: (54, 34),
    }
    state = _initial_state(holder_id=8, formation=home, away_positions=away)
    rise_text = (
        "O meia domina e levanta a cabeça enquanto a zaga visitante sobe junta, em "
        "linha, e deixa o centroavante para trás."
    )
    rise = advance_carry_scene(
        state,
        _event(
            1,
            MatchEventType.CARRY,
            (8,),
            rise_text,
            outcome="progressed",
        ),
        NormalizedPoint(60, 50),
        shape=INTERLOCKING_BLOCKS,
        supporting_destinations={
            **_fixed(
                MatchSide.HOME,
                {1: (6, 50), 9: (74, 50), 7: (67, 20), 11: (67, 80)},
            ),
            **_fixed(
                MatchSide.AWAY,
                {
                    1: (88, 50),
                    2: (68, 82), 3: (68, 60), 4: (68, 40), 6: (68, 18),
                    5: (60, 72), 8: (60, 50), 10: (60, 28),
                    7: (52, 66), 9: (52, 50), 11: (52, 34),
                },
            ),
        },
        duration_ms=1800,
    )
    pass_text = (
        "No momento do passe o centroavante está além da linha da zaga: "
        "impedimento marcado e a jogada é interrompida."
    )
    offside_pass = advance_pass_scene(
        rise.end_state,
        _event(2, MatchEventType.PASS, (8, 9), pass_text, outcome="offside"),
        shape=INTERLOCKING_BLOCKS,
        supporting_destinations={
            **_hold_all(rise.end_state, except_ids={(MatchSide.HOME, 9)}),
            (MatchSide.HOME, 9): NormalizedPoint(76, 50),
        },
    )
    return _scenario_snapshot(
        "movement-offside-trap-success",
        "Linha de impedimento bem-sucedida",
        "A zaga sobe junta antes do passe; quando a bola é tocada, o centroavante está impedido.",
        "movement",
        "players",
        state,
        (rise, offside_pass),
    )


def _overlap_fullback_scenario() -> dict[str, object]:
    """Ultrapassagem: o ponta corta para dentro, o lateral passa por fora e recebe
    o passe no espaço à sua frente."""

    home = {
        1: (6, 50),
        3: (30, 40), 4: (30, 60), 2: (44, 18), 6: (58, 88),
        5: (52, 28), 8: (54, 50), 10: (56, 68),
        7: (66, 20), 9: (70, 50), 11: (64, 80),
    }
    away = {
        1: (94, 50),
        2: (76, 80), 3: (80, 60), 4: (80, 40), 6: (76, 18),
        5: (64, 86), 8: (64, 50), 10: (64, 30),
        7: (52, 62), 9: (50, 50), 11: (52, 38),
    }
    state = _initial_state(holder_id=11, formation=home, away_positions=away)
    cut_text = (
        "O ponta direita corta para dentro e leva o lateral adversário junto, "
        "enquanto o lateral direito passa por fora."
    )
    cut = advance_carry_scene(
        state,
        _event(
            1,
            MatchEventType.CARRY,
            (11,),
            cut_text,
            lane=FieldLane.RIGHT,
            outcome="progressed",
        ),
        NormalizedPoint(72, 68),
        shape=INTERLOCKING_BLOCKS,
        supporting_destinations={
            **_fixed(MatchSide.HOME, {6: (68, 92)}),
            # O marcador acompanha o ponta para dentro e deixa a ultrapassagem livre.
            **_fixed(MatchSide.AWAY, {2: (73, 72), 5: (66, 86)}),
        },
        duration_ms=1600,
    )
    give_text = "O ponta toca no espaço à frente do lateral, que chega em velocidade pelo corredor."
    give = advance_pass_scene(
        cut.end_state,
        replace(
            _event(2, MatchEventType.PASS, (11, 6), give_text, lane=FieldLane.RIGHT),
            origin_zone=FieldZone(FieldThird.ATTACKING, FieldLane.RIGHT),
            destination_zone=FieldZone(FieldThird.ATTACKING, FieldLane.RIGHT),
        ),
        shape=INTERLOCKING_BLOCKS,
        supporting_destinations={
            **_fixed(MatchSide.HOME, {6: (80, 92)}),
            **_fixed(MatchSide.AWAY, {2: (73, 72), 5: (74, 89)}),
        },
        duration_ms=1600,
    )
    return _scenario_snapshot(
        "ball-overlap-fullback",
        "Ultrapassagem do lateral",
        "Ponta corta para dentro, lateral ultrapassa por fora e recebe no espaço.",
        "ball",
        "ball",
        state,
        (cut, give),
    )


def _counter_attack_scenario() -> dict[str, object]:
    """Contra-ataque: passe vertical pelo centro, pontas em corridas diagonais e
    finalização em velocidade contra uma defesa desorganizada."""

    home = {
        1: (6, 50),
        3: (28, 40), 4: (28, 60), 2: (30, 16), 6: (30, 84),
        5: (38, 30), 8: (44, 50), 10: (38, 70),
        7: (50, 20), 9: (52, 50), 11: (50, 80),
    }
    away = {
        1: (92, 50),
        3: (66, 42), 4: (66, 58), 2: (68, 22), 6: (68, 78),
        5: (56, 32), 8: (54, 50), 10: (56, 68),
        7: (42, 66), 9: (38, 48), 11: (42, 34),
    }
    state = _initial_state(holder_id=8, formation=home, away_positions=away)
    shape = CollectiveShape(
        forward_only=True,
        defending_retreat_ratio=1.0,
        defender_line_ratio=0.7,
        defender_min_x=8,
    )
    first_text = "Após a recuperação, o meia acha o centroavante pelo meio, em velocidade."
    first = advance_pass_scene(
        state,
        _event(1, MatchEventType.PASS, (8, 9), first_text),
        shape=shape,
        supporting_destinations=_fixed(
            MatchSide.HOME,
            {9: (62, 50), 7: (63, 26), 11: (63, 74), 8: (48, 51), 1: (6, 50)},
        ),
        duration_ms=2000,
    )
    second_text = "O centroavante abre para o ponta direita, que ataca a diagonal."
    second = advance_pass_scene(
        first.end_state,
        replace(
            _event(2, MatchEventType.PASS, (9, 11), second_text, lane=FieldLane.RIGHT),
            origin_zone=FieldZone(FieldThird.MIDDLE, FieldLane.CENTER),
            destination_zone=FieldZone(FieldThird.ATTACKING, FieldLane.RIGHT),
        ),
        shape=shape,
        supporting_destinations=_fixed(
            MatchSide.HOME,
            {11: (74, 72), 9: (72, 50), 7: (72, 34), 8: (58, 52), 1: (6, 50)},
        ),
        duration_ms=1600,
    )
    shot_text = "O ponta finaliza no canto enquanto os companheiros chegam à área."
    shot = advance_shot_scene(
        second.end_state,
        _event(
            3,
            MatchEventType.SHOT,
            (11,),
            shot_text,
            lane=FieldLane.RIGHT,
            outcome="on_target",
        ),
        NormalizedPoint(99, 53),
        shape=shape,
        supporting_destinations=_fixed(
            MatchSide.HOME,
            {9: (84, 52), 7: (83, 40), 8: (70, 52), 1: (6, 50)},
        ),
        duration_ms=1600,
    )
    return _scenario_snapshot(
        "ball-counter-attack",
        "Contra-ataque em velocidade",
        "Passe vertical, corridas diagonais dos pontas e finalização contra defesa desorganizada.",
        "ball",
        "ball",
        state,
        (first, second, shot),
    )


def _high_press_scenario() -> dict[str, object]:
    """Pressão alta: o passe para trás do adversário é o gatilho; o time da casa sobe
    junto, fecha as linhas de passe e pressiona o goleiro."""

    home = {
        1: (12, 50),
        3: (50, 42), 4: (50, 58), 2: (50, 20), 6: (50, 80),
        5: (60, 32), 8: (60, 50), 10: (60, 68),
        7: (72, 32), 9: (74, 50), 11: (72, 68),
    }
    away = {
        1: (94, 50),
        3: (84, 42), 4: (84, 58), 2: (78, 16), 6: (78, 84),
        5: (70, 30), 8: (70, 50), 10: (70, 70),
        7: (58, 72), 9: (56, 50), 11: (58, 28),
    }
    state = _initial_state(
        holder_id=3,
        formation=home,
        away_positions=away,
        holder_side=MatchSide.AWAY,
    )
    description = (
        "O passe para trás do zagueiro ao goleiro é o gatilho: o time da casa sobe "
        "junto, o centroavante pressiona o goleiro e os pontas fecham os zagueiros."
    )
    event = replace(
        _event(1, MatchEventType.PASS, (3, 1), description),
        team_side=MatchSide.AWAY,
        origin_zone=FieldZone(FieldThird.DEFENSIVE, FieldLane.CENTER),
        destination_zone=FieldZone(FieldThird.DEFENSIVE, FieldLane.CENTER),
    )
    advance = advance_pass_scene(
        state,
        event,
        shape=CollectiveShape(forward_only=True, defender_min_x=8),
        supporting_destinations=_fixed(
            MatchSide.HOME,
            {
                1: (22, 50),
                2: (60, 24), 3: (60, 44), 4: (60, 56), 6: (60, 76),
                5: (72, 36), 8: (72, 50), 10: (72, 64),
                7: (82, 38), 9: (88, 50), 11: (82, 62),
            },
        ),
        duration_ms=2000,
    )
    return _scenario_snapshot(
        "movement-high-press",
        "Pressão alta no passe para trás",
        description,
        "movement",
        "players",
        state,
        (advance,),
    )


def _short_goal_kick_scenario() -> dict[str, object]:
    """Tiro de meta curto: zagueiros abertos dentro da área, laterais altos e largos,
    e o adversário pressionando à frente da área."""

    home = {
        1: (5, 50),
        3: (11, 32), 4: (11, 68),
        2: (30, 10), 6: (30, 90),
        5: (32, 30), 8: (34, 50), 10: (32, 70),
        7: (46, 18), 9: (50, 50), 11: (46, 82),
    }
    away = {
        1: (94, 50),
        2: (68, 83), 3: (68, 61), 4: (68, 39), 6: (68, 17),
        5: (54, 73), 8: (54, 50), 10: (54, 27),
        7: (27, 62), 9: (25, 50), 11: (27, 38),
    }
    state = _initial_state(holder_id=1, formation=home, away_positions=away)
    description = (
        "Tiro de meta curto: o goleiro toca para o zagueiro aberto dentro da área "
        "enquanto o adversário pressiona e os laterais sobem para dar amplitude."
    )
    event = replace(
        _event(1, MatchEventType.PASS, (1, 4), description),
        origin_zone=FieldZone(FieldThird.DEFENSIVE, FieldLane.CENTER),
        destination_zone=FieldZone(FieldThird.DEFENSIVE, FieldLane.RIGHT),
    )
    advance = advance_pass_scene(
        state,
        event,
        shape=CollectiveShape(
            forward_only=True,
            defending_retreat_ratio=0.0,
            defender_line_ratio=0.5,
            defender_min_x=8,
        ),
        supporting_destinations={
            **_fixed(MatchSide.HOME, {1: (6, 52), 4: (13, 70)}),
            # O adversário fecha a linha de passe: pressão sobre o receptor.
            **_fixed(
                MatchSide.AWAY,
                {7: (22, 64), 9: (24, 52), 11: (25, 40)},
            ),
        },
        duration_ms=1400,
    )
    return _scenario_snapshot(
        "ball-goal-kick-short",
        "Tiro de meta curto",
        description,
        "ball",
        "ball",
        state,
        (advance,),
    )


def _one_two_scenario() -> dict[str, object]:
    """Tabela (parede): o meia toca para o centroavante, corre para além da marcação e
    recebe de volta em profundidade."""

    state = _initial_state(holder_id=8, formation=INTERLOCKED_HOME_POSITIONS)
    first_text = "O meia toca para o centroavante, que segura a bola de costas."
    second_text = "O centroavante devolve de primeira para o meia, que apareceu na frente."
    first = advance_pass_scene(
        state,
        _event(1, MatchEventType.PASS, (8, 9), first_text),
        shape=INTERLOCKING_BLOCKS,
        supporting_destinations=_fixed(
            MatchSide.HOME, {8: (50, 58), 9: (54, 50)}
        ),
        duration_ms=1800,
    )
    second = advance_pass_scene(
        first.end_state,
        _event(2, MatchEventType.PASS, (9, 8), second_text),
        shape=INTERLOCKING_BLOCKS,
        supporting_destinations=_fixed(
            MatchSide.HOME, {8: (62, 60), 9: (55, 50)}
        ),
        duration_ms=1800,
    )
    return _scenario_snapshot(
        "ball-one-two",
        "Tabela com o centroavante",
        "Troca de passes em um-dois: o meia passa, ultrapassa a marcação e recebe de volta.",
        "ball",
        "ball",
        state,
        (first, second),
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
    holder_side: MatchSide = MatchSide.HOME,
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
        ball_position=NormalizedPoint(
            *(
                home_positions[holder_id]
                if holder_side is MatchSide.HOME
                else away_positions[holder_id]
            )
        ),
        ball_holder_side=holder_side,
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
