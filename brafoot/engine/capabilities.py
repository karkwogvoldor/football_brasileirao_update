"""Deterministic and explainable capabilities derived from player profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isclose

from brafoot.engine.attributes import (
    MAX_ATTRIBUTE_VALUE,
    MIN_ATTRIBUTE_VALUE,
    PlayerProfile,
)


REFERENCE_HEIGHT_CM = (160, 205)
REFERENCE_WEIGHT_KG = (55, 105)


class SprintContext(str, Enum):
    """The distance profile of a straight-line run."""

    SHORT = "short"
    LONG = "long"


class AerialPhase(str, Enum):
    """Whether a player contests an aerial ball while attacking or defending."""

    ATTACKING = "attacking"
    DEFENDING = "defending"


@dataclass(frozen=True, slots=True)
class AbilityContribution:
    """One visible source used to calculate a derived capability."""

    source: str
    raw_value: float
    weight: float
    weighted_value: float


@dataclass(frozen=True, slots=True)
class DerivedAbility:
    """A 1-to-20 capability with an auditable calculation breakdown."""

    score: float
    contributions: tuple[AbilityContribution, ...]

    def contribution(self, source: str) -> AbilityContribution:
        """Return one named contribution from the calculation."""

        for item in self.contributions:
            if item.source == source:
                return item
        raise KeyError(source)


def calculate_sprint_ability(
    profile: PlayerProfile,
    context: SprintContext,
) -> DerivedAbility:
    """Calculate short or long straight-line running capacity.

    Height and weight are deliberately absent because acceleration, speed and
    endurance already describe the observed running capacity. Including body
    measurements again would count the same physical effect twice.
    """

    attributes = profile.attributes
    if context is SprintContext.SHORT:
        sources = (
            ("aceleracao", attributes.aceleracao, 0.65),
            ("velocidade", attributes.velocidade, 0.30),
            ("resistencia", attributes.resistencia, 0.05),
        )
    else:
        sources = (
            ("aceleracao", attributes.aceleracao, 0.25),
            ("velocidade", attributes.velocidade, 0.65),
            ("resistencia", attributes.resistencia, 0.10),
        )
    return derive_weighted_ability(sources)


def calculate_aerial_ability(
    profile: PlayerProfile,
    phase: AerialPhase,
) -> DerivedAbility:
    """Calculate access to and execution of an attacking or defensive header."""

    attributes = profile.attributes
    positioning = (
        attributes.posicionamento_ofensivo
        if phase is AerialPhase.ATTACKING
        else attributes.posicionamento_defensivo
    )
    positioning_source = (
        "posicionamento_ofensivo"
        if phase is AerialPhase.ATTACKING
        else "posicionamento_defensivo"
    )
    return derive_weighted_ability(
        (
            ("altura", _normalize_fact(profile.height_cm, REFERENCE_HEIGHT_CM), 0.15),
            ("impulsao", attributes.impulsao, 0.20),
            ("forca", attributes.forca, 0.10),
            ("antecipacao", attributes.antecipacao, 0.15),
            ("cabeceio", attributes.cabeceio, 0.20),
            (positioning_source, positioning, 0.20),
        )
    )


def calculate_physical_duel_ability(profile: PlayerProfile) -> DerivedAbility:
    """Calculate capacity to withstand and impose contact in a ground duel."""

    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("forca", attributes.forca, 0.45),
            ("equilibrio", attributes.equilibrio, 0.25),
            ("peso", _normalize_fact(profile.weight_kg, REFERENCE_WEIGHT_KG), 0.15),
            ("antecipacao", attributes.antecipacao, 0.15),
        )
    )


def derive_weighted_ability(
    sources: tuple[tuple[str, float, float], ...],
) -> DerivedAbility:
    """Build an explainable ability from named values whose weights total one."""

    total_weight = sum(weight for _, _, weight in sources)
    if not isclose(total_weight, 1.0):
        raise ValueError("Os pesos de uma capacidade derivada devem somar 1.")

    contributions = tuple(
        AbilityContribution(
            source=source,
            raw_value=float(raw_value),
            weight=weight,
            weighted_value=float(raw_value) * weight,
        )
        for source, raw_value, weight in sources
    )
    return DerivedAbility(
        score=sum(item.weighted_value for item in contributions),
        contributions=contributions,
    )


def _normalize_fact(value: int, reference_range: tuple[int, int]) -> float:
    lower, upper = reference_range
    bounded_value = min(max(value, lower), upper)
    proportion = (bounded_value - lower) / (upper - lower)
    return MIN_ATTRIBUTE_VALUE + proportion * (
        MAX_ATTRIBUTE_VALUE - MIN_ATTRIBUTE_VALUE
    )
