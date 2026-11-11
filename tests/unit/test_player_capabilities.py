from dataclasses import fields, replace

import pytest

from brafoot.engine.attributes import (
    ExceptionalTrait,
    PlayerAttributes,
    PlayerPosition,
    PlayerProfile,
    PreferredFoot,
)
from brafoot.engine.capabilities import (
    AerialPhase,
    SprintContext,
    calculate_aerial_ability,
    calculate_physical_duel_ability,
    calculate_sprint_ability,
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


# Produz sempre o mesmo valor e expõe contribuições que somam o resultado.
def test_derived_capability_is_deterministic_and_explainable():
    profile = make_profile(
        attributes=make_attributes(aceleracao=18, velocidade=16, resistencia=12)
    )

    first = calculate_sprint_ability(profile, SprintContext.SHORT)
    second = calculate_sprint_ability(profile, SprintContext.SHORT)

    assert first == second
    assert sum(item.weighted_value for item in first.contributions) == pytest.approx(
        first.score
    )
    assert first.contribution("aceleracao").raw_value == 18


# Valoriza mais aceleração em corrida curta e mais velocidade em corrida longa.
def test_sprint_context_changes_the_attribute_priority():
    explosive = make_profile(
        attributes=make_attributes(aceleracao=18, velocidade=12)
    )
    fast_over_distance = make_profile(
        attributes=make_attributes(aceleracao=12, velocidade=18)
    )

    assert calculate_sprint_ability(
        explosive, SprintContext.SHORT
    ).score > calculate_sprint_ability(
        fast_over_distance, SprintContext.SHORT
    ).score
    assert calculate_sprint_ability(
        fast_over_distance, SprintContext.LONG
    ).score > calculate_sprint_ability(explosive, SprintContext.LONG).score


# Não usa peso nem altura novamente quando os atributos de corrida já os representam.
def test_body_measurements_do_not_double_count_in_sprint_ability():
    lighter = make_profile(height_cm=165, weight_kg=60)
    heavier = make_profile(height_cm=200, weight_kg=100)

    assert calculate_sprint_ability(
        lighter, SprintContext.LONG
    ) == calculate_sprint_ability(heavier, SprintContext.LONG)


# Aumenta o alcance aéreo pela altura sem alterar a técnica de cabeceio armazenada.
def test_height_improves_aerial_ability_without_changing_heading_technique():
    shorter = make_profile(height_cm=165)
    taller = make_profile(height_cm=200)

    shorter_result = calculate_aerial_ability(shorter, AerialPhase.ATTACKING)
    taller_result = calculate_aerial_ability(taller, AerialPhase.ATTACKING)

    assert taller_result.score > shorter_result.score
    assert taller.attributes.cabeceio == shorter.attributes.cabeceio == 10
    assert taller_result.contribution("cabeceio").raw_value == 10


# Usa o posicionamento correspondente à fase ofensiva ou defensiva da disputa aérea.
def test_aerial_phase_uses_the_corresponding_positioning_attribute():
    profile = make_profile(
        attributes=make_attributes(
            posicionamento_ofensivo=18,
            posicionamento_defensivo=6,
        )
    )

    attacking = calculate_aerial_ability(profile, AerialPhase.ATTACKING)
    defending = calculate_aerial_ability(profile, AerialPhase.DEFENDING)

    assert attacking.score > defending.score
    assert attacking.contribution("posicionamento_ofensivo").raw_value == 18
    assert defending.contribution("posicionamento_defensivo").raw_value == 6


# Mantém a força como influência principal e o peso apenas como contexto moderado.
def test_strength_matters_more_than_weight_in_physical_duel():
    strong = make_profile(weight_kg=75, attributes=make_attributes(forca=15))
    heavier = make_profile(weight_kg=90, attributes=make_attributes(forca=10))

    assert calculate_physical_duel_ability(
        strong
    ).score > calculate_physical_duel_ability(heavier).score


# Limita medidas corporais extremas à faixa de referência do cálculo derivado.
def test_extreme_body_measurements_keep_capabilities_in_attribute_scale():
    minimum = make_profile(height_cm=140, weight_kg=40, attributes=make_attributes())
    maximum = make_profile(height_cm=220, weight_kg=130, attributes=make_attributes())

    minimum_aerial = calculate_aerial_ability(minimum, AerialPhase.ATTACKING)
    maximum_duel = calculate_physical_duel_ability(maximum)

    assert 1 <= minimum_aerial.score <= 20
    assert 1 <= maximum_duel.score <= 20


# Não aplica características excepcionais antes de existir uma situação específica.
def test_exceptional_traits_do_not_silently_change_base_capabilities():
    regular = make_profile()
    specialist = replace(
        regular,
        exceptional_traits=frozenset({ExceptionalTrait.HEADING_SPECIALIST}),
    )

    assert calculate_aerial_ability(
        regular, AerialPhase.ATTACKING
    ) == calculate_aerial_ability(specialist, AerialPhase.ATTACKING)
