from dataclasses import fields

import pytest

from brafoot.engine.attributes import (
    PlayerAttributes,
    PlayerPosition,
    PlayerProfile,
    PreferredFoot,
)
from brafoot.engine.capabilities import SprintContext
from brafoot.engine.contests import (
    ContestOutcome,
    compare_aerial_duel,
    compare_physical_duel,
    compare_sprint,
)


def make_attributes(**overrides: int) -> PlayerAttributes:
    values = {field.name: 10 for field in fields(PlayerAttributes)}
    values.update(overrides)
    return PlayerAttributes(**values)


def make_profile(**overrides: object) -> PlayerProfile:
    values = {
        "height_cm": 180,
        "weight_kg": 75,
        "preferred_foot": PreferredFoot.RIGHT,
        "origin_positions": (PlayerPosition.MIDFIELDER,),
        "attributes": make_attributes(),
    }
    values.update(overrides)
    return PlayerProfile(**values)


# Declara empate quando os dois jogadores possuem a mesma capacidade derivada.
def test_equal_players_produce_an_even_contest():
    result = compare_sprint(
        make_profile(),
        make_profile(),
        SprintContext.SHORT,
    )

    assert result.outcome is ContestOutcome.EVEN
    assert result.margin == 0
    assert result.normalized_margin == 0


# Identifica o jogador explosivo como favorito numa corrida curta.
def test_short_sprint_favors_the_more_explosive_player():
    explosive = make_profile(attributes=make_attributes(aceleracao=18, velocidade=12))
    long_runner = make_profile(attributes=make_attributes(aceleracao=12, velocidade=18))

    result = compare_sprint(explosive, long_runner, SprintContext.SHORT)

    assert result.outcome is ContestOutcome.FIRST
    assert result.margin > 0


# Inverte a vantagem quando a velocidade máxima domina uma corrida longa.
def test_long_sprint_favors_the_player_with_more_top_speed():
    explosive = make_profile(attributes=make_attributes(aceleracao=18, velocidade=12))
    long_runner = make_profile(attributes=make_attributes(aceleracao=12, velocidade=18))

    result = compare_sprint(explosive, long_runner, SprintContext.LONG)

    assert result.outcome is ContestOutcome.SECOND
    assert result.margin < 0


# Compara o posicionamento ofensivo do atacante com o defensivo do marcador.
def test_aerial_duel_uses_each_side_specific_phase():
    attacker = make_profile(
        attributes=make_attributes(
            posicionamento_ofensivo=18,
            posicionamento_defensivo=1,
        )
    )
    defender = make_profile(
        attributes=make_attributes(
            posicionamento_ofensivo=1,
            posicionamento_defensivo=6,
        )
    )

    result = compare_aerial_duel(attacker, defender)

    assert result.outcome is ContestOutcome.FIRST
    assert result.first.contribution("posicionamento_ofensivo").raw_value == 18
    assert result.second.contribution("posicionamento_defensivo").raw_value == 6


# Permite que leitura defensiva e impulsão superem uma diferença moderada de altura.
def test_aerial_defender_can_overcome_height_with_relevant_attributes():
    tall_attacker = make_profile(
        height_cm=195,
        attributes=make_attributes(
            impulsao=8,
            antecipacao=8,
            cabeceio=8,
            posicionamento_ofensivo=8,
        ),
    )
    prepared_defender = make_profile(
        height_cm=180,
        attributes=make_attributes(
            impulsao=17,
            antecipacao=17,
            cabeceio=15,
            posicionamento_defensivo=18,
        ),
    )

    result = compare_aerial_duel(tall_attacker, prepared_defender)

    assert result.outcome is ContestOutcome.SECOND


# Mantém força e equilíbrio decisivos no confronto físico terrestre.
def test_physical_duel_favors_strength_and_balance():
    stronger = make_profile(
        weight_kg=75,
        attributes=make_attributes(forca=17, equilibrio=16),
    )
    heavier = make_profile(
        weight_kg=95,
        attributes=make_attributes(forca=10, equilibrio=10),
    )

    result = compare_physical_duel(stronger, heavier)

    assert result.outcome is ContestOutcome.FIRST


# Normaliza a margem entre menos um e um sem apagar a diferença original.
def test_contest_exposes_original_and_normalized_margin():
    dominant = make_profile(
        attributes=make_attributes(aceleracao=20, velocidade=20, resistencia=20)
    )
    limited = make_profile(
        attributes=make_attributes(aceleracao=1, velocidade=1, resistencia=1)
    )

    result = compare_sprint(dominant, limited, SprintContext.LONG)

    assert result.margin == pytest.approx(19)
    assert result.normalized_margin == pytest.approx(1)


# Preserva o detalhamento dos dois jogadores para explicar o resultado do confronto.
def test_contest_preserves_both_capability_breakdowns():
    first = make_profile(attributes=make_attributes(forca=16))
    second = make_profile(attributes=make_attributes(forca=12))

    result = compare_physical_duel(first, second)

    assert result.first.contribution("forca").raw_value == 16
    assert result.second.contribution("forca").raw_value == 12
