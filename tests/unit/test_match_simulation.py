from dataclasses import fields, replace

import pytest

from brafoot.engine.attributes import (
    PlayerAttributes,
    PlayerPosition,
    PlayerProfile,
    PreferredFoot,
)
from brafoot.engine.clock import MatchPeriod, REGULATION_MATCH_SECONDS
from brafoot.engine.events import MatchEventType, validate_event_timeline
from brafoot.engine.matches import MatchSide
from brafoot.engine.randomness import DeterministicStream
from brafoot.engine.rulesets import SimulationRuleset
from brafoot.engine.sectors import LineupPlayer
from brafoot.engine.segments import SegmentStopReason, advance_match_segment
from brafoot.engine.simulation import (
    build_simulated_team,
    simulate_match,
    simulate_match_segment,
    SimulatedTeam,
)
from brafoot.engine.state import MatchState

LAYOUT = (
    PlayerPosition.GOALKEEPER,
    PlayerPosition.CENTRE_BACK,
    PlayerPosition.CENTRE_BACK,
    PlayerPosition.RIGHT_BACK,
    PlayerPosition.LEFT_BACK,
    PlayerPosition.DEFENSIVE_MIDFIELDER,
    PlayerPosition.MIDFIELDER,
    PlayerPosition.MIDFIELDER,
    PlayerPosition.WINGER,
    PlayerPosition.WINGER,
    PlayerPosition.STRIKER,
)


def make_team(side: MatchSide, level: int = 10):
    base_id = 1 if side is MatchSide.HOME else 101
    players = []
    for offset, position in enumerate(LAYOUT):
        values = {field.name: level for field in fields(PlayerAttributes)}
        profile = PlayerProfile(
            height_cm=180,
            weight_kg=75,
            preferred_foot=PreferredFoot.RIGHT,
            origin_positions=(position,),
            attributes=PlayerAttributes(**values),
        )
        players.append(LineupPlayer(base_id + offset, position, profile))
    return build_simulated_team(side, players)


def make_ruleset() -> SimulationRuleset:
    return SimulationRuleset(version="2026.1")


def start_state(seed: int = 7) -> MatchState:
    return MatchState.start(
        ruleset=make_ruleset(), kickoff_side=MatchSide.HOME, random_seed=seed
    )


# Os sorteios dependem só da semente e da posição, e retomar da posição salva continua a mesma sequência.
def test_deterministic_stream_is_reproducible_and_resumable():
    first = DeterministicStream(99)
    draws = [first.random() for _ in range(5)]
    resumed = DeterministicStream(99, step=3)

    assert draws[0] == DeterministicStream(99).random()
    assert [resumed.random() for _ in range(2)] == draws[3:]
    assert all(0.0 <= value < 1.0 for value in draws)
    assert first.step == 5
    assert DeterministicStream(100).random() != draws[0]


# Sorteios ponderados respeitam pesos e rejeitam entradas inválidas.
def test_deterministic_stream_weighted_choice_and_validation():
    stream = DeterministicStream(1)

    assert all(stream.choose(("a", "b"), (0.0, 1.0)) == "b" for _ in range(20))
    with pytest.raises(ValueError):
        stream.choose(("a",), (0.0,))
    with pytest.raises(ValueError):
        stream.choose(("a", "b"), (1.0,))
    with pytest.raises(ValueError):
        DeterministicStream(-1)


# A mesma entrada com a mesma semente gera exatamente os mesmos eventos e o mesmo estado final.
def test_segment_simulation_is_repeatable_for_the_same_input():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)

    first = simulate_match_segment(start_state(), make_ruleset(), home, away)
    second = simulate_match_segment(start_state(), make_ruleset(), home, away)

    assert first == second
    assert first.events


# Sementes diferentes produzem partidas diferentes.
def test_different_seeds_produce_different_matches():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)

    first = simulate_match(make_ruleset(), home, away, random_seed=1)
    second = simulate_match(make_ruleset(), home, away, random_seed=2)

    assert first.events != second.events


# O segmento para exatamente no limite do relógio e todos os eventos ficam dentro dele, em ordem.
def test_segment_events_stay_inside_the_segment_and_in_order():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)
    ruleset = make_ruleset()
    state = start_state()

    result = simulate_match_segment(state, ruleset, home, away, next_sequence=10)

    expected_end = advance_match_segment(state, ruleset).end_state.clock
    assert result.end_state.clock == expected_end
    assert result.stop_reason is SegmentStopReason.DURATION_LIMIT
    assert result.events[0].event_type is MatchEventType.PERIOD_START
    assert [event.sequence for event in result.events] == list(
        range(10, 10 + len(result.events))
    )
    assert result.next_sequence == 10 + len(result.events)
    assert validate_event_timeline(result.events) == ()
    assert all(
        state.clock.elapsed_seconds <= event.clock.elapsed_seconds < expected_end.elapsed_seconds
        for event in result.events
    )
    assert result.end_state.random_step > state.random_step


# O estado persistido no meio da partida retoma exatamente a mesma partida.
def test_resuming_from_a_persisted_snapshot_matches_an_uninterrupted_match():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)
    ruleset = make_ruleset()
    whole = simulate_match(ruleset, home, away, random_seed=21)

    state = start_state(21)
    events = []
    sequence = 1
    for _ in range(5):
        result = simulate_match_segment(
            state, ruleset, home, away, next_sequence=sequence
        )
        events.extend(result.events)
        sequence = result.next_sequence
        state = MatchState.from_snapshot(result.end_state.to_snapshot())

    assert tuple(events) == whole.events[: len(events)]


# Uma partida inteira atravessa intervalo e fim de jogo, com início e fim de cada período.
def test_full_match_has_period_boundaries_and_monotonic_timeline():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)

    match = simulate_match(make_ruleset(), home, away, random_seed=5)

    assert match.segments == REGULATION_MATCH_SECONDS // 180
    assert match.final_state.clock.period is MatchPeriod.FULL_TIME
    assert validate_event_timeline(match.events) == ()
    types = [event.event_type for event in match.events]
    assert types.count(MatchEventType.PERIOD_START) == 2
    assert types.count(MatchEventType.PERIOD_END) == 2
    assert types[0] is MatchEventType.PERIOD_START
    assert types[-1] is MatchEventType.PERIOD_END
    assert match.events[-1].clock.period is MatchPeriod.FULL_TIME


# O placar final é a soma dos eventos de gol, e cada gol vem logo depois de uma finalização no alvo.
def test_score_equals_goal_events_and_goals_follow_on_target_shots():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)

    for seed in range(15):
        match = simulate_match(make_ruleset(), home, away, random_seed=seed)
        goals = match.goal_events
        assert match.final_state.home_score == sum(
            1 for goal in goals if goal.team_side is MatchSide.HOME
        )
        assert match.final_state.away_score == sum(
            1 for goal in goals if goal.team_side is MatchSide.AWAY
        )
        for index, event in enumerate(match.events):
            if event.event_type is MatchEventType.GOAL:
                shot = match.events[index - 1]
                assert shot.event_type is MatchEventType.SHOT
                assert shot.outcome == "on_target"
                assert shot.participant_ids == event.participant_ids


# Os participantes pertencem à equipe que age, exceto o segundo jogador de um duelo.
def test_event_participants_belong_to_the_acting_team():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)
    teams = {MatchSide.HOME: home, MatchSide.AWAY: away}

    match = simulate_match(make_ruleset(), home, away, random_seed=3)

    for event in match.events:
        if event.team_side is None:
            continue
        own = teams[event.team_side].player_ids
        other = teams[
            MatchSide.AWAY if event.team_side is MatchSide.HOME else MatchSide.HOME
        ].player_ids
        if event.event_type is MatchEventType.DUEL:
            assert event.participant_ids[0] in own
            assert event.participant_ids[1] in other
        else:
            assert set(event.participant_ids) <= own


# A bola é contínua: quem recebe um passe ou cruzamento completo é quem age no lance seguinte da mesma equipe.
def test_ball_holder_is_continuous_between_consecutive_actions():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)
    match = simulate_match(make_ruleset(), home, away, random_seed=8)
    actions = {
        MatchEventType.PASS,
        MatchEventType.CARRY,
        MatchEventType.CROSS,
        MatchEventType.SHOT,
        MatchEventType.DUEL,
    }
    checked = 0

    for previous, current in zip(match.events, match.events[1:]):
        if (
            previous.event_type in {MatchEventType.PASS, MatchEventType.CROSS}
            and previous.outcome == "completed"
            and current.event_type in actions
            and current.team_side is previous.team_side
        ):
            assert current.participant_ids[0] == previous.participant_ids[1]
            checked += 1
        if (
            previous.event_type is MatchEventType.CARRY
            and current.event_type in actions
            and current.team_side is previous.team_side
        ):
            assert current.participant_ids[0] == previous.participant_ids[0]
            checked += 1

    assert checked > 50


# Depois de um gol a próxima ação é do time que sofreu, que reinicia a partir do círculo central.
def test_goal_hands_the_kickoff_to_the_conceded_side():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)
    checked = 0

    for seed in range(20):
        match = simulate_match(make_ruleset(), home, away, random_seed=seed)
        for goal, following in zip(match.events, match.events[1:]):
            if (
                goal.event_type is MatchEventType.GOAL
                and following.team_side is not None
            ):
                assert following.team_side is not goal.team_side
                checked += 1

    assert checked > 10


# Entradas inválidas são recusadas: jogadores repetidos, ruleset diferente e lados trocados.
def test_simulation_rejects_invalid_inputs():
    home, away = make_team(MatchSide.HOME), make_team(MatchSide.AWAY)
    other_ruleset = SimulationRuleset(version="outra")

    with pytest.raises(ValueError, match="distintos"):
        simulate_match_segment(
            start_state(),
            make_ruleset(),
            home,
            SimulatedTeam(
                side=MatchSide.AWAY,
                players=home.players,
                goalkeeper_id=home.goalkeeper_id,
                ratings=home.ratings,
            ),
        )
    with pytest.raises(ValueError, match="ruleset"):
        simulate_match_segment(start_state(), other_ruleset, home, away)
    with pytest.raises(ValueError, match="mandante"):
        simulate_match_segment(start_state(), make_ruleset(), away, home)


# Uma equipe só é válida com onze jogadores e exatamente um goleiro.
def test_simulated_team_requires_eleven_players_and_one_goalkeeper():
    team = make_team(MatchSide.HOME)

    with pytest.raises(ValueError, match="11"):
        build_simulated_team(MatchSide.HOME, team.players[:10])
    no_keeper = tuple(
        replace(player, assigned_position=PlayerPosition.MIDFIELDER)
        if player.assigned_position is PlayerPosition.GOALKEEPER
        else player
        for player in team.players
    )
    with pytest.raises(ValueError, match="goleiro"):
        build_simulated_team(MatchSide.HOME, no_keeper)


def _summarize(home_level: int, away_level: int, matches: int):
    home = make_team(MatchSide.HOME, home_level)
    away = make_team(MatchSide.AWAY, away_level)
    totals = {"goals": 0, "home_wins": 0, "away_wins": 0, "draws": 0, "shots": 0}
    for seed in range(matches):
        match = simulate_match(make_ruleset(), home, away, random_seed=seed)
        home_score, away_score = (
            match.final_state.home_score,
            match.final_state.away_score,
        )
        totals["goals"] += home_score + away_score
        totals["home_wins"] += home_score > away_score
        totals["away_wins"] += away_score > home_score
        totals["draws"] += home_score == away_score
        totals["shots"] += sum(
            1 for event in match.events if event.event_type is MatchEventType.SHOT
        )
    return {key: value / matches for key, value in totals.items()}


# Bateria de equilíbrio: times iguais geram gols, chutes, empates e mando próximos do futebol real.
@pytest.mark.slow
def test_balanced_teams_produce_realistic_distribution_and_home_advantage():
    summary = _summarize(10, 10, 300)

    assert 2.2 <= summary["goals"] <= 3.1  # gols por jogo
    assert 20 <= summary["shots"] <= 32  # chutes por jogo, somando os dois times
    assert 0.15 <= summary["draws"] <= 0.35
    assert summary["home_wins"] > summary["away_wins"]  # mando de campo favorece a casa


# Bateria de força: o time melhor vence mais, nas duas posições, sem eliminar o acaso.
@pytest.mark.slow
def test_stronger_team_wins_more_often_but_not_always():
    home_strong = _summarize(12, 9, 200)
    away_strong = _summarize(9, 12, 200)

    assert home_strong["home_wins"] > 0.55
    assert away_strong["away_wins"] > 0.55
    assert home_strong["away_wins"] > 0.02  # o time fraco ainda vence às vezes
    assert away_strong["home_wins"] > 0.02
