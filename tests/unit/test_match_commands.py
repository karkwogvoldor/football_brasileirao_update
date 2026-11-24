from dataclasses import FrozenInstanceError

import pytest

from brafoot.engine.commands import (
    AssignedPlayer,
    CommandInterruption,
    CommandValidationError,
    MatchTeamSelection,
    Substitution,
    SubstitutionCommand,
    apply_substitution_command,
)
from brafoot.engine.lineups import AvailabilityStatus, Lineup, Starter
from brafoot.engine.matches import MatchSide
from brafoot.engine.rulesets import SimulationRuleset


def make_lineup(club_id: int = 10) -> Lineup:
    starters = tuple(
        Starter(
            player_id=player_id,
            club_id=club_id,
            position="GOL" if player_id == 1 else "ATA",
        )
        for player_id in range(1, 12)
    )
    return Lineup(
        club_id=club_id,
        formation="4-3-3",
        starters=starters,
        designated_goalkeeper_id=1,
    )


def make_bench(club_id: int = 10) -> tuple[Starter, ...]:
    return tuple(
        Starter(
            player_id=player_id,
            club_id=club_id,
            position="GOL" if player_id == 12 else "ATA",
        )
        for player_id in range(12, 19)
    )


def make_selection(**overrides) -> MatchTeamSelection:
    values = {
        "side": MatchSide.HOME,
        "club_id": 10,
        "formation": "4-3-3",
        "on_field": tuple(
            AssignedPlayer(starter, starter.position)
            for starter in make_lineup().starters
        ),
        "bench": make_bench(),
        "designated_goalkeeper_id": 1,
        "substitutions_used": 0,
        "substitution_windows_used": 0,
        "substituted_out_player_ids": (),
    }
    values.update(overrides)
    return MatchTeamSelection(**values)


def make_command(*substitutions: Substitution) -> SubstitutionCommand:
    return SubstitutionCommand(
        sequence=1,
        side=MatchSide.HOME,
        substitutions=substitutions
        or (Substitution(player_out_id=11, player_in_id=13, assigned_position="ATA"),),
    )


# Constrói uma seleção ativa válida a partir da escalação e do banco confirmados.
def test_match_team_selection_starts_from_lineup_and_bench():
    selection = MatchTeamSelection.from_lineup(
        side=MatchSide.AWAY,
        lineup=make_lineup(20),
        bench=make_bench(20),
    )

    assert selection.side is MatchSide.AWAY
    assert len(selection.on_field) == 11
    assert tuple(player.player_id for player in selection.bench) == tuple(range(12, 19))
    assert selection.designated_goalkeeper_id == 1
    assert selection.substitutions_used == 0
    assert selection.substitution_windows_used == 0


# Rejeita uma seleção ativa que já contenha jogador indisponível em campo.
def test_match_team_selection_requires_valid_on_field_lineup():
    on_field = list(make_selection().on_field)
    on_field[-1] = AssignedPlayer(
        Starter(11, 10, "ATA", AvailabilityStatus.SUSPENDED),
        "ATA",
    )

    with pytest.raises(ValueError, match="suspensos"):
        make_selection(on_field=tuple(on_field))


# Mantém seleção e comando imutáveis para preservar segmentos já confirmados.
def test_match_command_domain_objects_are_immutable():
    selection = make_selection()
    command = make_command()

    with pytest.raises(FrozenInstanceError):
        selection.substitutions_used = 1
    with pytest.raises(FrozenInstanceError):
        command.sequence = 2


# Aplica uma troca somente na nova seleção e preserva a seleção anterior.
def test_substitution_replaces_player_only_in_future_selection():
    selection = make_selection()

    result = apply_substitution_command(
        selection,
        make_command(),
        SimulationRuleset(version="2026.1"),
        CommandInterruption.SEGMENT_BOUNDARY,
    )

    assert result.previous_selection is selection
    assert result.selection.player_ids == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13)
    assert tuple(player.player_id for player in result.selection.bench) == (
        12,
        14,
        15,
        16,
        17,
        18,
    )
    assert result.selection.substituted_out_player_ids == (11,)
    assert selection.player_ids == tuple(range(1, 12))


# Conta várias trocas simultâneas como uma única janela de substituição.
def test_substitution_batch_uses_one_window():
    command = make_command(
        Substitution(10, 13, "ATA"),
        Substitution(11, 14, "ATA"),
    )

    result = apply_substitution_command(
        make_selection(),
        command,
        SimulationRuleset(version="2026.1"),
        CommandInterruption.SEGMENT_BOUNDARY,
    )

    assert result.selection.substitutions_used == 2
    assert result.selection.substitution_windows_used == 1


# Não consome janela no intervalo quando o ruleset mantém a regra padrão.
def test_half_time_substitution_does_not_use_window_by_default():
    result = apply_substitution_command(
        make_selection(),
        make_command(),
        SimulationRuleset(version="2026.1"),
        CommandInterruption.HALF_TIME,
    )

    assert result.selection.substitutions_used == 1
    assert result.selection.substitution_windows_used == 0


# Permite que uma versão de regras conte a troca no intervalo como janela.
def test_ruleset_can_count_half_time_as_substitution_window():
    result = apply_substitution_command(
        make_selection(),
        make_command(),
        SimulationRuleset(
            version="2026.1",
            half_time_substitution_consumes_window=True,
        ),
        CommandInterruption.HALF_TIME,
    )

    assert result.selection.substitution_windows_used == 1


# Rejeita a aplicação enquanto não existe uma interrupção confirmada.
def test_substitution_requires_confirmed_interruption():
    with pytest.raises(CommandValidationError) as error:
        apply_substitution_command(
            make_selection(),
            make_command(),
            SimulationRuleset(version="2026.1"),
            None,
        )

    assert [violation.code for violation in error.value.violations] == [
        "invalid_interruption"
    ]


# Rejeita de forma agregada jogadores fora do campo, fora do banco ou indisponíveis.
def test_substitution_reports_invalid_participants_together():
    bench = make_bench() + (
        Starter(19, 10, "ATA", AvailabilityStatus.INJURED),
    )
    command = make_command(
        Substitution(99, 98, "ATA"),
        Substitution(10, 19, "ATA"),
    )

    with pytest.raises(CommandValidationError) as error:
        apply_substitution_command(
            make_selection(bench=bench),
            command,
            SimulationRuleset(version="2026.1"),
            CommandInterruption.SEGMENT_BOUNDARY,
        )

    assert [violation.code for violation in error.value.violations] == [
        "player_not_on_field",
        "player_not_on_bench",
        "player_not_available",
    ]


# Impede exceder quantidade de trocas e janelas configuradas no ruleset.
@pytest.mark.parametrize(
    ("selection", "ruleset", "expected_code"),
    [
        (
            make_selection(substitutions_used=5),
            SimulationRuleset(version="2026.1"),
            "substitution_limit_exceeded",
        ),
        (
            make_selection(substitution_windows_used=3),
            SimulationRuleset(version="2026.1"),
            "substitution_window_limit_exceeded",
        ),
    ],
)
def test_substitution_respects_ruleset_limits(selection, ruleset, expected_code):
    with pytest.raises(CommandValidationError) as error:
        apply_substitution_command(
            selection,
            make_command(),
            ruleset,
            CommandInterruption.SEGMENT_BOUNDARY,
        )

    assert expected_code in [violation.code for violation in error.value.violations]


# Exige que a troca do goleiro também designe seu substituto para o gol.
def test_goalkeeper_substitution_requires_replacement_goalkeeper():
    with pytest.raises(CommandValidationError) as error:
        apply_substitution_command(
            make_selection(),
            make_command(Substitution(1, 12, "ATA")),
            SimulationRuleset(version="2026.1"),
            CommandInterruption.SEGMENT_BOUNDARY,
        )

    assert [violation.code for violation in error.value.violations] == [
        "goalkeeper_replacement_required"
    ]


# Atualiza a designação do goleiro quando a troca mantém alguém no gol.
def test_goalkeeper_substitution_updates_designated_player():
    result = apply_substitution_command(
        make_selection(),
        make_command(Substitution(1, 12, "GOL")),
        SimulationRuleset(version="2026.1"),
        CommandInterruption.SEGMENT_BOUNDARY,
    )

    assert result.selection.designated_goalkeeper_id == 12
    assert result.selection.on_field[0].assigned_position == "GOL"


# Persiste e restaura seleção e comando sem perder tipos do domínio.
def test_selection_and_command_snapshot_round_trip_is_lossless():
    selection = make_selection()
    command = make_command(
        Substitution(10, 13, "ATA"),
        Substitution(11, 14, "ATA"),
    )

    assert MatchTeamSelection.from_snapshot(selection.to_snapshot()) == selection
    assert SubstitutionCommand.from_snapshot(command.to_snapshot()) == command


# Rejeita comandos com jogadores repetidos ou posições ambíguas antes da aplicação.
@pytest.mark.parametrize(
    "substitutions",
    [
        (Substitution(10, 13, "ATA"), Substitution(10, 14, "ATA")),
        (Substitution(10, 13, "ATA"), Substitution(11, 13, "ATA")),
    ],
)
def test_substitution_command_requires_unique_players(substitutions):
    with pytest.raises(ValueError, match="jogadores"):
        make_command(*substitutions)
