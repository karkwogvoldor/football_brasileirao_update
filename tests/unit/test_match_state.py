from dataclasses import FrozenInstanceError

import pytest

from brafoot.engine.clock import MatchClock, MatchPeriod
from brafoot.engine.matches import MatchSide
from brafoot.engine.rulesets import SimulationRuleset
from brafoot.engine.state import MatchCheckpoint, MatchState
from brafoot.engine.zones import FieldLane, FieldThird, FieldZone


def make_state(**overrides) -> MatchState:
    values = {
        "clock": MatchClock.start(),
        "home_score": 0,
        "away_score": 0,
        "possession": MatchSide.HOME,
        "ball_zone": FieldZone(FieldThird.MIDDLE, FieldLane.CENTER),
        "ruleset_version": "2026.1",
        "random_seed": 12345,
        "random_step": 0,
    }
    values.update(overrides)
    return MatchState(**values)


# Cria o estado inicial com placar zerado e bola no centro para o lado do pontapé.
def test_match_state_starts_from_ruleset_and_kickoff_side():
    state = MatchState.start(
        ruleset=SimulationRuleset(version="2026.1"),
        kickoff_side=MatchSide.AWAY,
        random_seed=9876,
    )

    assert state.clock == MatchClock.start()
    assert (state.home_score, state.away_score) == (0, 0)
    assert state.possession is MatchSide.AWAY
    assert state.ball_zone == FieldZone(FieldThird.MIDDLE, FieldLane.CENTER)
    assert state.ruleset_version == "2026.1"
    assert state.random_seed == 9876
    assert state.random_step == 0


# Mantém o estado imutável para impedir alteração retroativa de um segmento confirmado.
def test_match_state_is_immutable():
    state = make_state()

    with pytest.raises(FrozenInstanceError):
        state.home_score = 1


# Rejeita placares negativos e valores booleanos como gols válidos.
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("home_score", -1),
        ("away_score", -1),
        ("home_score", True),
        ("away_score", False),
    ],
)
def test_match_state_rejects_invalid_scores(field, value):
    with pytest.raises(ValueError, match="placar"):
        make_state(**{field: value})


# Rejeita posse ou zona que não usam os tipos estáveis do domínio.
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("possession", "home"),
        ("ball_zone", "middle_center"),
    ],
)
def test_match_state_requires_domain_types(field, value):
    with pytest.raises(ValueError, match="posse|zona"):
        make_state(**{field: value})


# Rejeita versões ambíguas e posições inválidas do gerador determinístico.
@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("ruleset_version", " 2026.1", "versão"),
        ("random_seed", True, "semente"),
        ("random_step", -1, "posição"),
        ("random_step", False, "posição"),
    ],
)
def test_match_state_rejects_invalid_determinism_metadata(field, value, message):
    with pytest.raises(ValueError, match=message):
        make_state(**{field: value})


# Gera um snapshot explícito e restaura exatamente o mesmo estado.
def test_match_state_snapshot_round_trip_is_lossless():
    state = make_state(
        clock=MatchClock(2750, MatchPeriod.SECOND_HALF),
        home_score=2,
        away_score=1,
        possession=MatchSide.AWAY,
        ball_zone=FieldZone(FieldThird.ATTACKING, FieldLane.RIGHT),
        random_step=17,
    )

    snapshot = state.to_snapshot()

    assert snapshot == {
        "elapsed_seconds": 2750,
        "period": "second_half",
        "home_score": 2,
        "away_score": 1,
        "possession": "away",
        "ball_zone": "attacking_right",
        "ruleset_version": "2026.1",
        "random_seed": 12345,
        "random_step": 17,
    }
    assert MatchState.from_snapshot(snapshot) == state


# Associa uma sequência monotônica ao estado preservado pelo checkpoint.
def test_match_checkpoint_preserves_sequence_and_state():
    state = make_state()

    checkpoint = MatchCheckpoint(sequence=3, state=state)

    assert checkpoint.sequence == 3
    assert checkpoint.state is state


# Rejeita sequências negativas e booleanas no checkpoint.
@pytest.mark.parametrize("sequence", [-1, True])
def test_match_checkpoint_requires_non_negative_integer_sequence(sequence):
    with pytest.raises(ValueError, match="sequência"):
        MatchCheckpoint(sequence=sequence, state=make_state())


# Persiste e restaura o checkpoint sem alterar seu estado interno.
def test_match_checkpoint_snapshot_round_trip_is_lossless():
    checkpoint = MatchCheckpoint(sequence=5, state=make_state())

    snapshot = checkpoint.to_snapshot()

    assert snapshot["sequence"] == 5
    assert snapshot["state"] == checkpoint.state.to_snapshot()
    assert MatchCheckpoint.from_snapshot(snapshot) == checkpoint
