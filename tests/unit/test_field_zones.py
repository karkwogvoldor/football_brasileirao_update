import pytest

from brafoot.engine.zones import (
    ALL_FIELD_ZONES,
    FieldLane,
    FieldThird,
    FieldZone,
    opposing_perspective,
)


# Mantém uma grade semântica fechada com três terços e três corredores.
def test_field_zone_catalog_contains_every_third_and_lane_combination():
    assert len(ALL_FIELD_ZONES) == 9
    assert set(ALL_FIELD_ZONES) == {
        FieldZone(third, lane)
        for third in FieldThird
        for lane in FieldLane
    }


# Produz um código estável para persistir e transmitir uma zona do campo.
@pytest.mark.parametrize(
    ("zone", "code"),
    [
        (
            FieldZone(FieldThird.DEFENSIVE, FieldLane.LEFT),
            "defensive_left",
        ),
        (
            FieldZone(FieldThird.MIDDLE, FieldLane.CENTER),
            "middle_center",
        ),
        (
            FieldZone(FieldThird.ATTACKING, FieldLane.RIGHT),
            "attacking_right",
        ),
    ],
)
def test_field_zone_has_stable_code(zone, code):
    assert zone.code == code
    assert FieldZone.from_code(code) == zone


# Rejeita um código que não representa uma combinação conhecida da grade.
def test_field_zone_rejects_unknown_code():
    with pytest.raises(ValueError, match="zona do campo"):
        FieldZone.from_code("penalty_area_center")


# Rejeita componentes livres para impedir zonas não versionadas no estado.
@pytest.mark.parametrize(
    ("third", "lane"),
    [
        ("defensive", FieldLane.LEFT),
        (FieldThird.DEFENSIVE, "left"),
    ],
)
def test_field_zone_requires_domain_enums(third, lane):
    with pytest.raises(ValueError, match="terço|corredor"):
        FieldZone(third, lane)


# Gira terço e corredor ao observar a mesma região pela equipe adversária.
def test_opposing_perspective_rotates_zone_by_one_hundred_eighty_degrees():
    zone = FieldZone(FieldThird.DEFENSIVE, FieldLane.LEFT)

    assert opposing_perspective(zone) == FieldZone(
        FieldThird.ATTACKING,
        FieldLane.RIGHT,
    )


# Mantém a região central do meio-campo igual nas duas perspectivas.
def test_opposing_perspective_preserves_middle_center():
    zone = FieldZone(FieldThird.MIDDLE, FieldLane.CENTER)

    assert opposing_perspective(zone) == zone


# Recupera a zona original depois de duas trocas de perspectiva.
@pytest.mark.parametrize("zone", ALL_FIELD_ZONES)
def test_opposing_perspective_is_reversible(zone):
    assert opposing_perspective(opposing_perspective(zone)) == zone
