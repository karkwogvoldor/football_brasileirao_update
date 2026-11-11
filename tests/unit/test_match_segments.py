from dataclasses import replace

import pytest

from brafoot.engine.clock import (
    REGULATION_HALF_SECONDS,
    REGULATION_MATCH_SECONDS,
    MatchClock,
    MatchPeriod,
)
from brafoot.engine.matches import MatchSide
from brafoot.engine.rulesets import SimulationRuleset
from brafoot.engine.segments import SegmentStopReason, advance_match_segment
from brafoot.engine.state import MatchState
from brafoot.engine.zones import FieldLane, FieldThird, FieldZone


def make_state(**overrides) -> MatchState:
    values = {
        "clock": MatchClock.start(),
        "home_score": 1,
        "away_score": 0,
        "possession": MatchSide.HOME,
        "ball_zone": FieldZone(FieldThird.ATTACKING, FieldLane.LEFT),
        "ruleset_version": "2026.1",
        "random_seed": 12345,
        "random_step": 7,
    }
    values.update(overrides)
    return MatchState(**values)


# Avança exatamente a duração padrão quando não encontra uma interrupção.
def test_match_segment_advances_by_ruleset_duration():
    state = make_state()

    result = advance_match_segment(
        state,
        SimulationRuleset(version="2026.1"),
    )

    assert result.start_state is state
    assert result.end_state.clock.elapsed_seconds == 180
    assert result.elapsed_seconds == 180
    assert result.stop_reason is SegmentStopReason.DURATION_LIMIT


# Respeita uma duração de segmento menor configurada no ruleset.
def test_match_segment_uses_custom_ruleset_duration():
    result = advance_match_segment(
        make_state(),
        SimulationRuleset(version="2026.1", segment_duration_seconds=60),
    )

    assert result.end_state.clock.elapsed_seconds == 60
    assert result.elapsed_seconds == 60


# Para no intervalo e informa somente os segundos efetivamente avançados.
def test_match_segment_stops_early_at_half_time():
    state = make_state(
        clock=MatchClock(
            REGULATION_HALF_SECONDS - 45,
            MatchPeriod.FIRST_HALF,
        )
    )

    result = advance_match_segment(
        state,
        SimulationRuleset(version="2026.1"),
    )

    assert result.end_state.clock == MatchClock(
        REGULATION_HALF_SECONDS,
        MatchPeriod.HALF_TIME,
    )
    assert result.elapsed_seconds == 45
    assert result.stop_reason is SegmentStopReason.HALF_TIME


# Para no fim da partida sem ultrapassar os noventa minutos.
def test_match_segment_stops_early_at_full_time():
    state = make_state(
        clock=MatchClock(
            REGULATION_MATCH_SECONDS - 30,
            MatchPeriod.SECOND_HALF,
        )
    )

    result = advance_match_segment(
        state,
        SimulationRuleset(version="2026.1"),
    )

    assert result.end_state.clock == MatchClock(
        REGULATION_MATCH_SECONDS,
        MatchPeriod.FULL_TIME,
    )
    assert result.elapsed_seconds == 30
    assert result.stop_reason is SegmentStopReason.FULL_TIME


# Preserva todos os campos que ainda não possuem eventos capazes de alterá-los.
def test_match_segment_only_changes_the_clock():
    state = make_state()

    result = advance_match_segment(
        state,
        SimulationRuleset(version="2026.1"),
    )

    assert result.end_state == replace(
        state,
        clock=MatchClock(180, MatchPeriod.FIRST_HALF),
    )
    assert state.clock == MatchClock.start()


# Produz exatamente o mesmo resultado para as mesmas entradas.
def test_match_segment_is_deterministic_for_the_same_input():
    state = make_state()
    ruleset = SimulationRuleset(version="2026.1")

    assert advance_match_segment(state, ruleset) == advance_match_segment(
        state,
        ruleset,
    )


# Rejeita um ruleset diferente daquele registrado no estado.
def test_match_segment_rejects_ruleset_version_mismatch():
    with pytest.raises(ValueError, match="versão"):
        advance_match_segment(
            make_state(),
            SimulationRuleset(version="2026.2"),
        )


# Rejeita o avanço enquanto a partida está no intervalo ou encerrada.
@pytest.mark.parametrize(
    "clock",
    [
        MatchClock(REGULATION_HALF_SECONDS, MatchPeriod.HALF_TIME),
        MatchClock(REGULATION_MATCH_SECONDS, MatchPeriod.FULL_TIME),
    ],
)
def test_match_segment_rejects_non_playing_periods(clock):
    with pytest.raises(ValueError, match="período"):
        advance_match_segment(
            make_state(clock=clock),
            SimulationRuleset(version="2026.1"),
        )
