import pytest

from brafoot.engine.clock import (
    REGULATION_HALF_SECONDS,
    REGULATION_MATCH_SECONDS,
    MatchClock,
    MatchPeriod,
    advance_match_clock,
    start_second_half,
)


# Inicia uma partida no primeiro tempo com o cronômetro zerado.
def test_match_clock_starts_at_the_beginning_of_first_half():
    clock = MatchClock.start()

    assert clock.elapsed_seconds == 0
    assert clock.period is MatchPeriod.FIRST_HALF
    assert clock.display == "00:00"


# Avança o relógio dentro do primeiro tempo sem alterar o período.
def test_match_clock_advances_inside_first_half():
    clock = advance_match_clock(MatchClock.start(), 125)

    assert clock.elapsed_seconds == 125
    assert clock.period is MatchPeriod.FIRST_HALF
    assert clock.display == "02:05"


# Encerra o segmento exatamente no intervalo sem consumir o segundo tempo.
def test_match_clock_stops_at_half_time_boundary():
    clock = MatchClock(
        elapsed_seconds=REGULATION_HALF_SECONDS - 30,
        period=MatchPeriod.FIRST_HALF,
    )

    result = advance_match_clock(clock, 180)

    assert result.elapsed_seconds == REGULATION_HALF_SECONDS
    assert result.period is MatchPeriod.HALF_TIME
    assert result.display == "45:00"


# Mantém o relógio parado no intervalo até uma transição explícita.
def test_match_clock_does_not_advance_during_half_time():
    clock = MatchClock(
        elapsed_seconds=REGULATION_HALF_SECONDS,
        period=MatchPeriod.HALF_TIME,
    )

    assert advance_match_clock(clock, 180) == clock


# Inicia o segundo tempo preservando os quarenta e cinco minutos ja jogados.
def test_second_half_starts_explicitly_after_half_time():
    half_time = MatchClock(
        elapsed_seconds=REGULATION_HALF_SECONDS,
        period=MatchPeriod.HALF_TIME,
    )

    second_half = start_second_half(half_time)

    assert second_half.elapsed_seconds == REGULATION_HALF_SECONDS
    assert second_half.period is MatchPeriod.SECOND_HALF


# Rejeita o inicio do segundo tempo fora do intervalo.
def test_second_half_cannot_start_outside_half_time():
    with pytest.raises(ValueError, match="intervalo"):
        start_second_half(MatchClock.start())


# Encerra a partida em noventa minutos sem ultrapassar o fim regulamentar.
def test_match_clock_stops_at_full_time_boundary():
    clock = MatchClock(
        elapsed_seconds=REGULATION_MATCH_SECONDS - 20,
        period=MatchPeriod.SECOND_HALF,
    )

    result = advance_match_clock(clock, 180)

    assert result.elapsed_seconds == REGULATION_MATCH_SECONDS
    assert result.period is MatchPeriod.FULL_TIME
    assert result.display == "90:00"


# Mantém imutável um relógio de partida já encerrada.
def test_match_clock_does_not_advance_after_full_time():
    clock = MatchClock(
        elapsed_seconds=REGULATION_MATCH_SECONDS,
        period=MatchPeriod.FULL_TIME,
    )

    assert advance_match_clock(clock, 180) == clock


# Rejeita estados de relógio incompatíveis com o período informado.
@pytest.mark.parametrize(
    ("elapsed_seconds", "period"),
    [
        (REGULATION_HALF_SECONDS, MatchPeriod.FIRST_HALF),
        (0, MatchPeriod.HALF_TIME),
        (REGULATION_HALF_SECONDS - 1, MatchPeriod.SECOND_HALF),
        (REGULATION_MATCH_SECONDS, MatchPeriod.SECOND_HALF),
        (REGULATION_MATCH_SECONDS - 1, MatchPeriod.FULL_TIME),
    ],
)
def test_match_clock_rejects_inconsistent_period_state(elapsed_seconds, period):
    with pytest.raises(ValueError, match="período"):
        MatchClock(elapsed_seconds=elapsed_seconds, period=period)


# Rejeita segundos negativos e booleanos na construção do estado do relógio.
@pytest.mark.parametrize("elapsed_seconds", [-1, True])
def test_match_clock_rejects_invalid_elapsed_seconds(elapsed_seconds):
    with pytest.raises(ValueError, match="segundo atual"):
        MatchClock(
            elapsed_seconds=elapsed_seconds,
            period=MatchPeriod.FIRST_HALF,
        )


# Rejeita durações negativas e booleanas como avanços válidos do relógio.
@pytest.mark.parametrize("seconds", [-1, True])
def test_match_clock_rejects_invalid_advance_duration(seconds):
    with pytest.raises(ValueError, match="duração"):
        advance_match_clock(MatchClock.start(), seconds)
