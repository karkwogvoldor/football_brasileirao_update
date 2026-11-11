"""Pure domain types for player characteristics and positional adaptation."""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum


MIN_ATTRIBUTE_VALUE = 1
MAX_ATTRIBUTE_VALUE = 20
IMPROVISED_POSITION_FACTOR = 0.95
DEFAULT_ORIGIN_POSITION_MATCHES = 10


class PreferredFoot(str, Enum):
    """A player's dominant foot."""

    LEFT = "left"
    RIGHT = "right"


class PlayerPosition(str, Enum):
    """Positions that an outfield player or goalkeeper may occupy."""

    GOALKEEPER = "GOL"
    CENTRE_BACK = "ZAG"
    FULL_BACK = "LAT"
    RIGHT_BACK = "LAD"
    LEFT_BACK = "LAE"
    DEFENSIVE_MIDFIELDER = "VOL"
    MIDFIELDER = "MEI"
    WINGER = "PT"
    SECOND_STRIKER = "SA"
    STRIKER = "ATA"


class ExceptionalTrait(str, Enum):
    """Rare positive or negative characteristics shown with a star."""

    CONTROVERSIAL = "polemico"
    NIGHTLIFE = "baladeiro"
    BIG_GAME_PLAYER = "tem_estrela"
    HEADING_SPECIALIST = "cabeceador"
    PENALTY_SAVER = "pegador_de_penalti"


class TraitImpact(str, Enum):
    """The usual direction of an exceptional trait's game effect."""

    POSITIVE = "positive"
    NEGATIVE = "negative"


@dataclass(frozen=True, slots=True)
class ExceptionalTraitDefinition:
    """Presentation and impact metadata for one exceptional trait."""

    label: str
    impact: TraitImpact
    symbol: str = "★"


EXCEPTIONAL_TRAITS: dict[ExceptionalTrait, ExceptionalTraitDefinition] = {
    ExceptionalTrait.CONTROVERSIAL: ExceptionalTraitDefinition(
        label="Polêmico",
        impact=TraitImpact.NEGATIVE,
    ),
    ExceptionalTrait.NIGHTLIFE: ExceptionalTraitDefinition(
        label="Baladeiro",
        impact=TraitImpact.NEGATIVE,
    ),
    ExceptionalTrait.BIG_GAME_PLAYER: ExceptionalTraitDefinition(
        label="Tem estrela",
        impact=TraitImpact.POSITIVE,
    ),
    ExceptionalTrait.HEADING_SPECIALIST: ExceptionalTraitDefinition(
        label="Cabeceador",
        impact=TraitImpact.POSITIVE,
    ),
    ExceptionalTrait.PENALTY_SAVER: ExceptionalTraitDefinition(
        label="Pegador de pênalti",
        impact=TraitImpact.POSITIVE,
    ),
}


class PlayerAttributeValidationError(ValueError):
    """Raised when one or more universal attributes are outside 1 to 20."""

    def __init__(self, invalid_attributes: tuple[str, ...]) -> None:
        self.invalid_attributes = invalid_attributes
        super().__init__(
            "Atributos devem ser números inteiros entre 1 e 20: "
            + ", ".join(invalid_attributes)
        )


@dataclass(frozen=True, slots=True)
class PlayerAttributes:
    """The same universal 1-to-20 attribute pool used by every player."""

    controle: int
    drible: int
    passe_curto: int
    passe_longo: int
    cruzamento: int
    finalizacao: int
    potencia_chute: int
    cabeceio: int
    desarme: int
    bola_parada: int
    pe_fraco: int

    aceleracao: int
    velocidade: int
    agilidade: int
    equilibrio: int
    forca: int
    impulsao: int
    resistencia: int

    visao: int
    antecipacao: int
    decisao: int
    compostura: int
    posicionamento_ofensivo: int
    posicionamento_defensivo: int
    concentracao: int
    trabalho_coletivo: int

    reflexos_goleiro: int
    manuseio_goleiro: int
    posicionamento_goleiro: int
    tecnica_aerea_goleiro: int

    def __post_init__(self) -> None:
        invalid_attributes = tuple(
            field.name
            for field in fields(self)
            if not _is_valid_attribute_value(getattr(self, field.name))
        )
        if invalid_attributes:
            raise PlayerAttributeValidationError(invalid_attributes)


@dataclass(frozen=True, slots=True)
class PlayerProfile:
    """Physical facts, origin positions, attributes and exceptional traits."""

    height_cm: int
    weight_kg: int
    preferred_foot: PreferredFoot
    origin_positions: tuple[PlayerPosition, ...]
    attributes: PlayerAttributes
    exceptional_traits: frozenset[ExceptionalTrait] = frozenset()

    def __post_init__(self) -> None:
        if self.height_cm <= 0:
            raise ValueError("A altura deve ser maior que zero.")
        if self.weight_kg <= 0:
            raise ValueError("O peso deve ser maior que zero.")
        if not self.origin_positions:
            raise ValueError("O jogador deve ter ao menos uma posição de origem.")
        if len(set(self.origin_positions)) != len(self.origin_positions):
            raise ValueError("As posições de origem não podem se repetir.")


def positional_factor(
    origin_positions: tuple[PlayerPosition, ...],
    assigned_position: PlayerPosition,
) -> float:
    """Return a small penalty for improvisation without blocking any position."""

    if assigned_position in origin_positions:
        return 1.0
    return IMPROVISED_POSITION_FACTOR


def promote_to_origin_position(
    origin_positions: tuple[PlayerPosition, ...],
    played_position: PlayerPosition,
    matches_played: int,
    *,
    required_matches: int = DEFAULT_ORIGIN_POSITION_MATCHES,
) -> tuple[PlayerPosition, ...]:
    """Add a played position to the origins after a configurable match count.

    Match counting belongs to the season/application layer. The engine receives
    only the current count and does not store positional experience or levels.
    """

    if matches_played < 0:
        raise ValueError("A quantidade de partidas não pode ser negativa.")
    if required_matches <= 0:
        raise ValueError("O limite de partidas deve ser maior que zero.")
    if played_position in origin_positions or matches_played < required_matches:
        return origin_positions
    return origin_positions + (played_position,)


def _is_valid_attribute_value(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and MIN_ATTRIBUTE_VALUE <= value <= MAX_ATTRIBUTE_VALUE
    )
