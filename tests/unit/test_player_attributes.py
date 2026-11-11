from dataclasses import fields

import pytest

from brafoot.engine.attributes import (
    DEFAULT_ORIGIN_POSITION_MATCHES,
    EXCEPTIONAL_TRAITS,
    IMPROVISED_POSITION_FACTOR,
    ExceptionalTrait,
    PlayerAttributeValidationError,
    PlayerAttributes,
    PlayerPosition,
    PlayerProfile,
    PreferredFoot,
    TraitImpact,
    positional_factor,
    promote_to_origin_position,
)


def make_attributes(**overrides: int) -> PlayerAttributes:
    values = {field.name: 10 for field in fields(PlayerAttributes)}
    values.update(overrides)
    return PlayerAttributes(**values)


# Mantém um conjunto universal e fechado de trinta atributos para todas as posições.
def test_player_attributes_have_the_expected_universal_pool():
    attribute_names = {field.name for field in fields(PlayerAttributes)}

    assert len(attribute_names) == 30
    assert "cabeceio" in attribute_names
    assert "cabecio" not in attribute_names


# Aceita os dois limites válidos da escala de atributos de um a vinte.
def test_player_attributes_accept_values_from_one_to_twenty():
    attributes = make_attributes(controle=1, tecnica_aerea_goleiro=20)

    assert attributes.controle == 1
    assert attributes.tecnica_aerea_goleiro == 20


# Rejeita de uma só vez todos os atributos fora da escala de um a vinte.
def test_player_attributes_report_every_value_outside_the_scale():
    with pytest.raises(PlayerAttributeValidationError) as error:
        make_attributes(controle=0, velocidade=21)

    assert error.value.invalid_attributes == ("controle", "velocidade")


# Rejeita booleanos para impedir que True e False sejam aceitos como notas numéricas.
def test_player_attributes_reject_boolean_values():
    with pytest.raises(PlayerAttributeValidationError) as error:
        make_attributes(decisao=True)

    assert error.value.invalid_attributes == ("decisao",)


# Mantém altura, peso e pé preferido fora da escala universal de atributos.
def test_player_profile_keeps_physical_facts_separate_from_attributes():
    profile = PlayerProfile(
        height_cm=180,
        weight_kg=75,
        preferred_foot=PreferredFoot.RIGHT,
        origin_positions=(PlayerPosition.MIDFIELDER,),
        attributes=make_attributes(),
        exceptional_traits=frozenset({ExceptionalTrait.BIG_GAME_PLAYER}),
    )

    assert profile.height_cm == 180
    assert profile.weight_kg == 75
    assert profile.exceptional_traits == frozenset(
        {ExceptionalTrait.BIG_GAME_PLAYER}
    )


# Rejeita um perfil sem nenhuma posição de origem consolidada.
def test_player_profile_requires_an_origin_position():
    with pytest.raises(ValueError, match="posição de origem"):
        PlayerProfile(
            height_cm=180,
            weight_kg=75,
            preferred_foot=PreferredFoot.LEFT,
            origin_positions=(),
            attributes=make_attributes(),
        )


# Permite qualquer improvisação com uma penalidade pequena e constante.
def test_improvised_position_is_always_allowed_with_small_penalty():
    factor = positional_factor(
        (PlayerPosition.WINGER,),
        PlayerPosition.FULL_BACK,
    )

    assert factor == IMPROVISED_POSITION_FACTOR
    assert factor == 0.95


# Não penaliza o jogador quando ele atua em uma de suas posições de origem.
def test_origin_position_has_no_positional_penalty():
    assert positional_factor(
        (PlayerPosition.WINGER, PlayerPosition.FULL_BACK),
        PlayerPosition.FULL_BACK,
    ) == 1.0


# Mantém o jogador improvisado antes de alcançar o limite configurado de partidas.
def test_position_is_not_promoted_before_required_match_count():
    origins = (PlayerPosition.WINGER,)

    result = promote_to_origin_position(
        origins,
        PlayerPosition.FULL_BACK,
        DEFAULT_ORIGIN_POSITION_MATCHES - 1,
    )

    assert result == origins


# Integra a função praticada às posições de origem ao atingir o limite de partidas.
def test_position_is_promoted_after_required_match_count():
    result = promote_to_origin_position(
        (PlayerPosition.WINGER,),
        PlayerPosition.FULL_BACK,
        DEFAULT_ORIGIN_POSITION_MATCHES,
    )

    assert result == (PlayerPosition.WINGER, PlayerPosition.FULL_BACK)


# Não duplica uma posição que já pertence ao conjunto de origens do jogador.
def test_origin_position_promotion_is_idempotent():
    origins = (PlayerPosition.WINGER, PlayerPosition.FULL_BACK)

    result = promote_to_origin_position(
        origins,
        PlayerPosition.FULL_BACK,
        DEFAULT_ORIGIN_POSITION_MATCHES + 20,
    )

    assert result == origins


# Cataloga características excepcionais positivas e negativas com o símbolo de estrela.
def test_exceptional_traits_have_impact_and_star_metadata():
    assert set(EXCEPTIONAL_TRAITS) == set(ExceptionalTrait)
    assert EXCEPTIONAL_TRAITS[ExceptionalTrait.CONTROVERSIAL].impact is (
        TraitImpact.NEGATIVE
    )
    assert EXCEPTIONAL_TRAITS[ExceptionalTrait.NIGHTLIFE].impact is (
        TraitImpact.NEGATIVE
    )
    assert EXCEPTIONAL_TRAITS[ExceptionalTrait.BIG_GAME_PLAYER].impact is (
        TraitImpact.POSITIVE
    )
    assert EXCEPTIONAL_TRAITS[ExceptionalTrait.HEADING_SPECIALIST].symbol == "★"
    assert EXCEPTIONAL_TRAITS[ExceptionalTrait.PENALTY_SAVER].symbol == "★"
