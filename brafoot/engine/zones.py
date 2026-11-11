"""Semantic field zones used by the pure simulation domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FieldThird(str, Enum):
    """Longitudinal thirds relative to the team being analysed."""

    DEFENSIVE = "defensive"
    MIDDLE = "middle"
    ATTACKING = "attacking"


class FieldLane(str, Enum):
    """Lateral lanes relative to the team being analysed."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class FieldZone:
    """One stable cell in the semantic three-by-three field grid."""

    third: FieldThird
    lane: FieldLane

    def __post_init__(self) -> None:
        if not isinstance(self.third, FieldThird):
            raise ValueError("O terço da zona do campo não é válido.")
        if not isinstance(self.lane, FieldLane):
            raise ValueError("O corredor da zona do campo não é válido.")

    @property
    def code(self) -> str:
        """Return the stable persistence code for this zone."""

        return f"{self.third.value}_{self.lane.value}"

    @classmethod
    def from_code(cls, code: str) -> FieldZone:
        """Restore a semantic zone from its exact persistence code."""

        if not isinstance(code, str):
            raise ValueError("O código da zona do campo não é válido.")
        try:
            third_value, lane_value = code.split("_", maxsplit=1)
            return cls(FieldThird(third_value), FieldLane(lane_value))
        except (TypeError, ValueError) as error:
            raise ValueError("O código da zona do campo não é válido.") from error


ALL_FIELD_ZONES = tuple(
    FieldZone(third, lane)
    for third in FieldThird
    for lane in FieldLane
)


def opposing_perspective(zone: FieldZone) -> FieldZone:
    """Rotate a semantic zone to the opposing team's perspective."""

    if not isinstance(zone, FieldZone):
        raise ValueError("A zona do campo não é válida.")

    opposite_third = {
        FieldThird.DEFENSIVE: FieldThird.ATTACKING,
        FieldThird.MIDDLE: FieldThird.MIDDLE,
        FieldThird.ATTACKING: FieldThird.DEFENSIVE,
    }[zone.third]
    opposite_lane = {
        FieldLane.LEFT: FieldLane.RIGHT,
        FieldLane.CENTER: FieldLane.CENTER,
        FieldLane.RIGHT: FieldLane.LEFT,
    }[zone.lane]
    return FieldZone(opposite_third, opposite_lane)
