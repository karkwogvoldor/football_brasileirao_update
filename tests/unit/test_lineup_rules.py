import json
from pathlib import Path

import pytest

from brafoot.engine.lineups import (
    AvailabilityStatus,
    Lineup,
    LineupValidationError,
    Starter,
    require_valid_lineup,
    validate_lineup,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def make_valid_lineup() -> Lineup:
    starters = (Starter(player_id=1, club_id=10, position="GOL"),) + tuple(
        Starter(player_id=player_id, club_id=10, position="LIN")
        for player_id in range(2, 12)
    )
    return Lineup(club_id=10, formation="4-3-3", starters=starters)


def violation_codes(lineup: Lineup) -> set[str]:
    return {violation.code for violation in validate_lineup(lineup)}


# Aceita uma escalação completa que satisfaz todas as regras básicas.
def test_valid_lineup_is_accepted():
    lineup = make_valid_lineup()

    assert validate_lineup(lineup) == ()
    assert require_valid_lineup(lineup) is None


# Rejeita qualquer quantidade de titulares diferente de onze.
def test_lineup_requires_exactly_eleven_starters():
    lineup = make_valid_lineup()
    lineup = Lineup(
        club_id=lineup.club_id,
        formation=lineup.formation,
        starters=lineup.starters[:-1],
    )

    assert violation_codes(lineup) == {"starter_count"}


# Rejeita o mesmo jogador escalado mais de uma vez entre os titulares.
def test_lineup_requires_distinct_players():
    lineup = make_valid_lineup()
    lineup = Lineup(
        club_id=lineup.club_id,
        formation=lineup.formation,
        starters=lineup.starters[:-1] + (lineup.starters[1],),
    )

    assert violation_codes(lineup) == {"duplicate_player"}


# Rejeita uma escalação sem goleiro.
def test_lineup_requires_one_goalkeeper():
    lineup = make_valid_lineup()
    starters = tuple(
        Starter(starter.player_id, starter.club_id, "LIN")
        for starter in lineup.starters
    )

    assert violation_codes(Lineup(10, "4-3-3", starters)) == {
        "goalkeeper_count"
    }


# Rejeita uma escalação com mais de um goleiro.
def test_lineup_rejects_multiple_goalkeepers():
    lineup = make_valid_lineup()
    starters = lineup.starters[:-1] + (Starter(11, 10, "GOL"),)

    assert violation_codes(Lineup(10, "4-3-3", starters)) == {
        "goalkeeper_count"
    }


# Aceita jogador de linha no gol quando o elenco não tem goleiro elegível.
def test_lineup_allows_emergency_goalkeeper_when_none_is_eligible():
    lineup = make_valid_lineup()
    starters = (Starter(1, 10, "LIN"),) + lineup.starters[1:]
    emergency_lineup = Lineup(
        club_id=10,
        formation="4-3-3",
        starters=starters,
        designated_goalkeeper_id=1,
        eligible_squad_goalkeeper_ids=(),
    )

    assert validate_lineup(emergency_lineup) == ()


# Rejeita o improviso quando existe goleiro natural elegível no elenco.
def test_lineup_rejects_emergency_goalkeeper_when_natural_keeper_is_eligible():
    lineup = make_valid_lineup()
    starters = (Starter(1, 10, "LIN"),) + lineup.starters[1:]
    emergency_lineup = Lineup(
        club_id=10,
        formation="4-3-3",
        starters=starters,
        designated_goalkeeper_id=1,
        eligible_squad_goalkeeper_ids=(12,),
    )

    assert violation_codes(emergency_lineup) == {
        "emergency_goalkeeper_not_allowed"
    }


# Rejeita o improviso se um goleiro natural elegível já está entre os titulares.
def test_lineup_rejects_emergency_keeper_with_eligible_starter_goalkeeper():
    lineup = make_valid_lineup()
    emergency_lineup = Lineup(
        club_id=10,
        formation="4-3-3",
        starters=lineup.starters,
        designated_goalkeeper_id=2,
        eligible_squad_goalkeeper_ids=(),
    )

    assert violation_codes(emergency_lineup) == {
        "emergency_goalkeeper_not_allowed"
    }


# Não autoriza goleiro improvisado quando a elegibilidade do elenco é desconhecida.
def test_lineup_rejects_emergency_goalkeeper_without_squad_eligibility_context():
    lineup = make_valid_lineup()
    starters = (Starter(1, 10, "LIN"),) + lineup.starters[1:]
    emergency_lineup = Lineup(
        club_id=10,
        formation="4-3-3",
        starters=starters,
        designated_goalkeeper_id=1,
    )

    assert violation_codes(emergency_lineup) == {
        "emergency_goalkeeper_not_allowed"
    }


# Rejeita como goleiro designado um jogador que não está entre os titulares.
def test_lineup_requires_designated_goalkeeper_to_be_a_starter():
    lineup = make_valid_lineup()
    invalid_lineup = Lineup(
        club_id=10,
        formation="4-3-3",
        starters=lineup.starters,
        designated_goalkeeper_id=99,
        eligible_squad_goalkeeper_ids=(),
    )

    assert violation_codes(invalid_lineup) == {"goalkeeper_count"}


# Rejeita titular cujo vínculo pertence a outro clube.
def test_lineup_requires_every_player_to_belong_to_club():
    lineup = make_valid_lineup()
    starters = lineup.starters[:-1] + (Starter(11, 20, "LIN"),)

    assert violation_codes(Lineup(10, "4-3-3", starters)) == {"foreign_player"}


# Aceita como titular um jogador explicitamente disponível para a partida.
def test_lineup_accepts_available_player():
    lineup = make_valid_lineup()
    starters = lineup.starters[:-1] + (
        Starter(11, 10, "LIN", AvailabilityStatus.AVAILABLE),
    )

    assert violation_codes(Lineup(10, "4-3-3", starters)) == set()


# Rejeita um jogador lesionado e informa seu identificador na infração.
def test_lineup_rejects_injured_player():
    lineup = make_valid_lineup()
    starters = lineup.starters[:-1] + (
        Starter(11, 10, "LIN", AvailabilityStatus.INJURED),
    )
    violations = validate_lineup(Lineup(10, "4-3-3", starters))

    assert [violation.code for violation in violations] == ["ineligible_player"]
    assert violations[0].player_ids == (11,)


# Rejeita um jogador suspenso e informa seu identificador na infração.
def test_lineup_rejects_suspended_player():
    lineup = make_valid_lineup()
    starters = lineup.starters[:-1] + (
        Starter(11, 10, "LIN", AvailabilityStatus.SUSPENDED),
    )
    violations = validate_lineup(Lineup(10, "4-3-3", starters))

    assert [violation.code for violation in violations] == ["ineligible_player"]
    assert violations[0].player_ids == (11,)


# Reúne todos os jogadores inelegíveis em uma única infração determinística.
def test_lineup_reports_all_ineligible_players():
    lineup = make_valid_lineup()
    starters = (
        lineup.starters[:-2]
        + (
            Starter(10, 10, "LIN", AvailabilityStatus.INJURED),
            Starter(11, 10, "LIN", AvailabilityStatus.SUSPENDED),
        )
    )
    violations = validate_lineup(Lineup(10, "4-3-3", starters))

    assert [violation.code for violation in violations] == ["ineligible_player"]
    assert violations[0].player_ids == (10, 11)


# Rejeita uma formação que não pertence ao catálogo tático suportado.
def test_lineup_requires_supported_formation():
    lineup = make_valid_lineup()

    assert violation_codes(Lineup(10, "2-2-6", lineup.starters)) == {
        "invalid_formation"
    }


# Expõe todas as infrações de uma escalação em uma única validação.
def test_require_valid_lineup_raises_with_all_violations():
    lineup = Lineup(
        club_id=10,
        formation="inválida",
        starters=(
            Starter(1, 20, "LIN", AvailabilityStatus.SUSPENDED),
            Starter(1, 20, "LIN"),
        ),
    )

    with pytest.raises(LineupValidationError) as error:
        require_valid_lineup(lineup)

    assert {violation.code for violation in error.value.violations} == {
        "starter_count",
        "duplicate_player",
        "goalkeeper_count",
        "foreign_player",
        "ineligible_player",
        "invalid_formation",
    }


# Garante que todas as escalações cadastradas satisfazem as regras da engine.
def test_registered_lineups_characterize_current_legacy_data():
    payload = json.loads(
        (PROJECT_ROOT / "data" / "brasileirao_2026_lineups.json").read_text(
            encoding="utf-8"
        )
    )
    results = {}

    for registered in payload["lineups"]:
        lineup = Lineup(
            club_id=registered["legacy_team_id"],
            formation=registered["formation"],
            starters=tuple(
                Starter(
                    player_id=starter["legacy_player_id"],
                    club_id=starter["legacy_team_id"],
                    position=starter["position"],
                )
                for starter in registered["starters"]
            ),
        )
        results[registered["club_slug"]] = violation_codes(lineup)

    assert len(results) == 20
    assert results["bahia"] == set()
    assert all(not violations for violations in results.values())
