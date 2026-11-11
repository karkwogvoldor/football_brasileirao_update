import pytest

from brafoot.engine.lineups import Lineup, Starter
from brafoot.engine.matches import (
    MatchSetup,
    MatchSide,
    MatchValidationError,
    require_valid_match,
    validate_match,
)


def make_valid_lineup(club_id: int, first_player_id: int) -> Lineup:
    starters = (
        Starter(first_player_id, club_id, "GOL"),
    ) + tuple(
        Starter(player_id, club_id, "LIN")
        for player_id in range(first_player_id + 1, first_player_id + 11)
    )
    return Lineup(club_id=club_id, formation="4-3-3", starters=starters)


def violation_codes(match: MatchSetup) -> list[str]:
    return [violation.code for violation in validate_match(match)]


# Aceita uma partida entre clubes diferentes com duas escalações válidas.
def test_valid_match_is_accepted():
    match = MatchSetup(
        home_lineup=make_valid_lineup(10, 1),
        away_lineup=make_valid_lineup(20, 101),
    )

    assert validate_match(match) == ()
    assert require_valid_match(match) is None


# Rejeita uma partida na qual o mesmo clube é mandante e visitante.
def test_match_requires_different_clubs():
    match = MatchSetup(
        home_lineup=make_valid_lineup(10, 1),
        away_lineup=make_valid_lineup(10, 101),
    )

    assert violation_codes(match) == ["clubs_must_differ"]


# Identifica e preserva os detalhes de uma escalação inválida do mandante.
def test_match_rejects_invalid_home_lineup():
    home = make_valid_lineup(10, 1)
    invalid_home = Lineup(10, "4-3-3", home.starters[:-1])
    match = MatchSetup(invalid_home, make_valid_lineup(20, 101))

    violations = validate_match(match)

    assert [violation.code for violation in violations] == ["invalid_home_lineup"]
    assert violations[0].side is MatchSide.HOME
    assert [item.code for item in violations[0].lineup_violations] == [
        "starter_count"
    ]


# Identifica e preserva os detalhes de uma escalação inválida do visitante.
def test_match_rejects_invalid_away_lineup():
    away = make_valid_lineup(20, 101)
    invalid_away = Lineup(20, "4-3-3", away.starters[:-1])
    match = MatchSetup(make_valid_lineup(10, 1), invalid_away)

    violations = validate_match(match)

    assert [violation.code for violation in violations] == ["invalid_away_lineup"]
    assert violations[0].side is MatchSide.AWAY
    assert [item.code for item in violations[0].lineup_violations] == [
        "starter_count"
    ]


# Retorna juntas as infrações da partida e das duas escalações.
def test_match_reports_all_violations_in_deterministic_order():
    home = make_valid_lineup(10, 1)
    away = make_valid_lineup(10, 101)
    match = MatchSetup(
        Lineup(10, "inválida", home.starters[:-1]),
        Lineup(10, "inválida", away.starters[:-1]),
    )

    with pytest.raises(MatchValidationError) as error:
        require_valid_match(match)

    assert [violation.code for violation in error.value.violations] == [
        "clubs_must_differ",
        "invalid_home_lineup",
        "invalid_away_lineup",
    ]
    assert [
        item.code
        for item in error.value.violations[1].lineup_violations
    ] == ["starter_count", "invalid_formation"]
    assert [
        item.code
        for item in error.value.violations[2].lineup_violations
    ] == ["starter_count", "invalid_formation"]
