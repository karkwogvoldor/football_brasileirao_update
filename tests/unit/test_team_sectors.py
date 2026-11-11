from dataclasses import fields

import pytest

from brafoot.engine.attributes import (
    IMPROVISED_POSITION_FACTOR,
    PlayerAttributes,
    PlayerPosition,
    PlayerProfile,
    PreferredFoot,
)
from brafoot.engine.sectors import (
    LineupPlayer,
    SectorCompositionError,
    calculate_team_sector_profile,
)


def make_attributes(**overrides: int) -> PlayerAttributes:
    values = {field.name: 10 for field in fields(PlayerAttributes)}
    values.update(overrides)
    return PlayerAttributes(**values)


def make_player(
    player_id: int,
    assigned_position: PlayerPosition,
    *,
    origin_position: PlayerPosition | None = None,
    attributes: PlayerAttributes | None = None,
    height_cm: int = 180,
    weight_kg: int = 75,
) -> LineupPlayer:
    return LineupPlayer(
        player_id=player_id,
        assigned_position=assigned_position,
        profile=PlayerProfile(
            height_cm=height_cm,
            weight_kg=weight_kg,
            preferred_foot=PreferredFoot.RIGHT,
            origin_positions=(origin_position or assigned_position,),
            attributes=attributes or make_attributes(),
        ),
    )


def make_team() -> tuple[LineupPlayer, ...]:
    return (
        make_player(1, PlayerPosition.GOALKEEPER),
        make_player(2, PlayerPosition.CENTRE_BACK),
        make_player(3, PlayerPosition.CENTRE_BACK),
        make_player(4, PlayerPosition.RIGHT_BACK),
        make_player(5, PlayerPosition.LEFT_BACK),
        make_player(6, PlayerPosition.DEFENSIVE_MIDFIELDER),
        make_player(7, PlayerPosition.MIDFIELDER),
        make_player(8, PlayerPosition.MIDFIELDER),
        make_player(9, PlayerPosition.WINGER),
        make_player(10, PlayerPosition.WINGER),
        make_player(11, PlayerPosition.STRIKER),
    )


# Produz quinze dimensões independentes sem criar uma nota geral do time.
def test_team_profile_keeps_sector_dimensions_separate():
    result = calculate_team_sector_profile(make_team())

    assert len(fields(result.defense)) == 5
    assert len(fields(result.midfield)) == 5
    assert len(fields(result.attack)) == 5
    assert not hasattr(result, "overall")


# Mantém os resultados setoriais independentes da ordem de entrada dos jogadores.
def test_team_profile_is_independent_from_player_order():
    players = make_team()

    first = calculate_team_sector_profile(players)
    reversed_result = calculate_team_sector_profile(tuple(reversed(players)))

    assert first == reversed_result


# Aumenta a defesa aérea quando um zagueiro melhora nas qualidades correspondentes.
def test_aerial_defender_improves_aerial_defense_dimension():
    baseline = make_team()
    specialist = make_player(
        2,
        PlayerPosition.CENTRE_BACK,
        height_cm=198,
        attributes=make_attributes(
            impulsao=18,
            forca=17,
            antecipacao=18,
            cabeceio=17,
            posicionamento_defensivo=18,
        ),
    )
    improved = (specialist,) + tuple(player for player in baseline if player.player_id != 2)

    assert calculate_team_sector_profile(
        improved
    ).defense.aerial_defense.score > calculate_team_sector_profile(
        baseline
    ).defense.aerial_defense.score


# Aumenta criação e progressão quando um meio-campista possui visão e passe superiores.
def test_creative_midfielder_improves_relevant_midfield_dimensions():
    baseline = make_team()
    creator = make_player(
        7,
        PlayerPosition.MIDFIELDER,
        attributes=make_attributes(
            visao=19,
            passe_curto=18,
            passe_longo=18,
            decisao=17,
            drible=16,
        ),
    )
    improved = (creator,) + tuple(player for player in baseline if player.player_id != 7)
    baseline_profile = calculate_team_sector_profile(baseline)
    improved_profile = calculate_team_sector_profile(improved)

    assert improved_profile.midfield.creation.score > baseline_profile.midfield.creation.score
    assert improved_profile.midfield.progression.score > (
        baseline_profile.midfield.progression.score
    )


# Aumenta a profundidade ofensiva sem alterar diretamente a defesa aérea.
def test_fast_attacker_improves_depth_without_changing_defensive_group():
    baseline = make_team()
    runner = make_player(
        9,
        PlayerPosition.WINGER,
        attributes=make_attributes(
            aceleracao=19,
            velocidade=19,
            posicionamento_ofensivo=17,
            antecipacao=16,
        ),
    )
    improved = (runner,) + tuple(player for player in baseline if player.player_id != 9)
    baseline_profile = calculate_team_sector_profile(baseline)
    improved_profile = calculate_team_sector_profile(improved)

    assert improved_profile.attack.depth.score > baseline_profile.attack.depth.score
    assert improved_profile.defense.aerial_defense == (
        baseline_profile.defense.aerial_defense
    )


# Aplica somente o pequeno redutor definido quando um jogador atua improvisado.
def test_improvised_player_contribution_keeps_small_positional_penalty():
    players = make_team()
    improvised = make_player(
        9,
        PlayerPosition.WINGER,
        origin_position=PlayerPosition.MIDFIELDER,
    )
    changed = (improvised,) + tuple(player for player in players if player.player_id != 9)

    result = calculate_team_sector_profile(changed)
    contribution = next(
        item for item in result.attack.depth.contributions if item.player_id == 9
    )

    assert contribution.positional_factor == IMPROVISED_POSITION_FACTOR
    assert contribution.adjusted_score == pytest.approx(
        contribution.ability.score * IMPROVISED_POSITION_FACTOR
    )


# Preserva a decomposição individual usada para explicar uma força coletiva.
def test_sector_metric_preserves_player_and_attribute_breakdowns():
    result = calculate_team_sector_profile(make_team())
    midfielder = next(
        item for item in result.midfield.control.contributions if item.player_id == 7
    )

    assert midfielder.ability.contribution("controle").raw_value == 10
    assert midfielder.ability.contribution("passe_curto").raw_value == 10


# Rejeita a composição quando uma das três linhas ou o goleiro está ausente.
def test_team_profile_reports_every_missing_role_group():
    only_defenders = tuple(
        player
        for player in make_team()
        if player.assigned_position
        in {
            PlayerPosition.GOALKEEPER,
            PlayerPosition.CENTRE_BACK,
            PlayerPosition.RIGHT_BACK,
            PlayerPosition.LEFT_BACK,
        }
    )

    with pytest.raises(SectorCompositionError) as error:
        calculate_team_sector_profile(only_defenders)

    assert error.value.missing_groups == ("midfield", "attack")


# Rejeita identificadores duplicados para não contabilizar o mesmo jogador duas vezes.
def test_team_profile_rejects_duplicate_players():
    players = make_team()
    duplicated = players + (players[-1],)

    with pytest.raises(ValueError, match="distintos"):
        calculate_team_sector_profile(duplicated)
