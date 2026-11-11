"""Multidimensional team strengths aggregated from assigned lineup roles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from brafoot.engine.attributes import (
    PlayerPosition,
    PlayerProfile,
    positional_factor,
)
from brafoot.engine.capabilities import (
    AerialPhase,
    DerivedAbility,
    SprintContext,
    calculate_aerial_ability,
    calculate_sprint_ability,
    derive_weighted_ability,
)


DEFENSIVE_POSITIONS = frozenset(
    {
        PlayerPosition.CENTRE_BACK,
        PlayerPosition.FULL_BACK,
        PlayerPosition.RIGHT_BACK,
        PlayerPosition.LEFT_BACK,
        PlayerPosition.DEFENSIVE_MIDFIELDER,
    }
)
MIDFIELD_POSITIONS = frozenset(
    {
        PlayerPosition.DEFENSIVE_MIDFIELDER,
        PlayerPosition.MIDFIELDER,
    }
)
ATTACK_POSITIONS = frozenset(
    {
        PlayerPosition.WINGER,
        PlayerPosition.SECOND_STRIKER,
        PlayerPosition.STRIKER,
    }
)


@dataclass(frozen=True, slots=True)
class LineupPlayer:
    """A player profile occupying one role in the submitted lineup."""

    player_id: int
    assigned_position: PlayerPosition
    profile: PlayerProfile


@dataclass(frozen=True, slots=True)
class PlayerSectorContribution:
    """One player's explainable contribution to a team-sector metric."""

    player_id: int
    ability: DerivedAbility
    positional_factor: float
    adjusted_score: float


@dataclass(frozen=True, slots=True)
class SectorMetric:
    """The average contribution of eligible lineup players to one dimension."""

    score: float
    contributions: tuple[PlayerSectorContribution, ...]


@dataclass(frozen=True, slots=True)
class DefenseSectorProfile:
    """Independent defensive dimensions; intentionally no defensive overall."""

    goalkeeper: SectorMetric
    central_protection: SectorMetric
    wide_protection: SectorMetric
    aerial_defense: SectorMetric
    recovery: SectorMetric


@dataclass(frozen=True, slots=True)
class MidfieldSectorProfile:
    """Independent midfield dimensions; intentionally no midfield overall."""

    control: SectorMetric
    progression: SectorMetric
    creation: SectorMetric
    recovery: SectorMetric
    pressing: SectorMetric


@dataclass(frozen=True, slots=True)
class AttackSectorProfile:
    """Independent attacking dimensions; intentionally no attacking overall."""

    depth: SectorMetric
    combination: SectorMetric
    aerial_presence: SectorMetric
    creation: SectorMetric
    finishing: SectorMetric


@dataclass(frozen=True, slots=True)
class TeamSectorProfile:
    """A lineup's multidimensional defensive, midfield and attacking profile."""

    defense: DefenseSectorProfile
    midfield: MidfieldSectorProfile
    attack: AttackSectorProfile


class SectorCompositionError(ValueError):
    """Raised when assigned roles cannot form every required team sector."""

    def __init__(self, missing_groups: tuple[str, ...]) -> None:
        self.missing_groups = missing_groups
        super().__init__("Setores sem jogadores atribuídos: " + ", ".join(missing_groups))


def calculate_team_sector_profile(
    players: tuple[LineupPlayer, ...],
) -> TeamSectorProfile:
    """Aggregate a valid lineup into 15 explainable dimensions."""

    player_ids = [player.player_id for player in players]
    if len(set(player_ids)) != len(player_ids):
        raise ValueError("Os jogadores do perfil setorial devem ser distintos.")

    goalkeepers = _players_in(players, {PlayerPosition.GOALKEEPER})
    defenders = _players_in(players, DEFENSIVE_POSITIONS)
    midfielders = _players_in(players, MIDFIELD_POSITIONS)
    attackers = _players_in(players, ATTACK_POSITIONS)
    groups = {
        "goalkeeper": goalkeepers,
        "defense": defenders,
        "midfield": midfielders,
        "attack": attackers,
    }
    missing_groups = tuple(name for name, group in groups.items() if not group)
    if missing_groups:
        raise SectorCompositionError(missing_groups)

    return TeamSectorProfile(
        defense=DefenseSectorProfile(
            goalkeeper=_aggregate(goalkeepers, _goalkeeper_ability),
            central_protection=_aggregate(defenders, _central_protection),
            wide_protection=_aggregate(defenders, _wide_protection),
            aerial_defense=_aggregate(
                defenders,
                lambda profile: calculate_aerial_ability(
                    profile, AerialPhase.DEFENDING
                ),
            ),
            recovery=_aggregate(defenders, _defensive_recovery),
        ),
        midfield=MidfieldSectorProfile(
            control=_aggregate(midfielders, _midfield_control),
            progression=_aggregate(midfielders, _midfield_progression),
            creation=_aggregate(midfielders, _midfield_creation),
            recovery=_aggregate(midfielders, _midfield_recovery),
            pressing=_aggregate(midfielders, _midfield_pressing),
        ),
        attack=AttackSectorProfile(
            depth=_aggregate(attackers, _attacking_depth),
            combination=_aggregate(attackers, _attacking_combination),
            aerial_presence=_aggregate(
                attackers,
                lambda profile: calculate_aerial_ability(
                    profile, AerialPhase.ATTACKING
                ),
            ),
            creation=_aggregate(attackers, _attacking_creation),
            finishing=_aggregate(attackers, _attacking_finishing),
        ),
    )


def _players_in(
    players: tuple[LineupPlayer, ...],
    positions: set[PlayerPosition] | frozenset[PlayerPosition],
) -> tuple[LineupPlayer, ...]:
    return tuple(
        sorted(
            (player for player in players if player.assigned_position in positions),
            key=lambda player: player.player_id,
        )
    )


def _aggregate(
    players: tuple[LineupPlayer, ...],
    evaluator: Callable[[PlayerProfile], DerivedAbility],
) -> SectorMetric:
    contributions = tuple(
        _player_contribution(player, evaluator(player.profile)) for player in players
    )
    return SectorMetric(
        score=sum(item.adjusted_score for item in contributions) / len(contributions),
        contributions=contributions,
    )


def _player_contribution(
    player: LineupPlayer,
    ability: DerivedAbility,
) -> PlayerSectorContribution:
    factor = positional_factor(
        player.profile.origin_positions,
        player.assigned_position,
    )
    return PlayerSectorContribution(
        player_id=player.player_id,
        ability=ability,
        positional_factor=factor,
        adjusted_score=ability.score * factor,
    )


def _goalkeeper_ability(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("reflexos_goleiro", attributes.reflexos_goleiro, 0.30),
            ("manuseio_goleiro", attributes.manuseio_goleiro, 0.25),
            ("posicionamento_goleiro", attributes.posicionamento_goleiro, 0.25),
            ("tecnica_aerea_goleiro", attributes.tecnica_aerea_goleiro, 0.20),
        )
    )


def _central_protection(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("posicionamento_defensivo", attributes.posicionamento_defensivo, 0.30),
            ("desarme", attributes.desarme, 0.25),
            ("antecipacao", attributes.antecipacao, 0.20),
            ("forca", attributes.forca, 0.15),
            ("concentracao", attributes.concentracao, 0.10),
        )
    )


def _wide_protection(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    short_sprint = calculate_sprint_ability(profile, SprintContext.SHORT).score
    long_sprint = calculate_sprint_ability(profile, SprintContext.LONG).score
    return derive_weighted_ability(
        (
            ("corrida_curta", short_sprint, 0.20),
            ("corrida_longa", long_sprint, 0.10),
            ("desarme", attributes.desarme, 0.20),
            ("posicionamento_defensivo", attributes.posicionamento_defensivo, 0.20),
            ("resistencia", attributes.resistencia, 0.15),
            ("agilidade", attributes.agilidade, 0.15),
        )
    )


def _defensive_recovery(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            (
                "corrida_curta",
                calculate_sprint_ability(profile, SprintContext.SHORT).score,
                0.35,
            ),
            (
                "corrida_longa",
                calculate_sprint_ability(profile, SprintContext.LONG).score,
                0.20,
            ),
            ("antecipacao", attributes.antecipacao, 0.20),
            ("posicionamento_defensivo", attributes.posicionamento_defensivo, 0.15),
            ("resistencia", attributes.resistencia, 0.10),
        )
    )


def _midfield_control(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("controle", attributes.controle, 0.25),
            ("passe_curto", attributes.passe_curto, 0.20),
            ("compostura", attributes.compostura, 0.20),
            ("decisao", attributes.decisao, 0.15),
            ("equilibrio", attributes.equilibrio, 0.10),
            ("trabalho_coletivo", attributes.trabalho_coletivo, 0.10),
        )
    )


def _midfield_progression(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("passe_curto", attributes.passe_curto, 0.15),
            ("passe_longo", attributes.passe_longo, 0.20),
            ("drible", attributes.drible, 0.20),
            ("visao", attributes.visao, 0.20),
            ("decisao", attributes.decisao, 0.15),
            ("velocidade", attributes.velocidade, 0.10),
        )
    )


def _midfield_creation(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("visao", attributes.visao, 0.30),
            ("passe_curto", attributes.passe_curto, 0.15),
            ("passe_longo", attributes.passe_longo, 0.15),
            ("cruzamento", attributes.cruzamento, 0.10),
            ("decisao", attributes.decisao, 0.15),
            ("posicionamento_ofensivo", attributes.posicionamento_ofensivo, 0.15),
        )
    )


def _midfield_recovery(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("desarme", attributes.desarme, 0.25),
            ("posicionamento_defensivo", attributes.posicionamento_defensivo, 0.25),
            ("antecipacao", attributes.antecipacao, 0.20),
            ("resistencia", attributes.resistencia, 0.15),
            ("trabalho_coletivo", attributes.trabalho_coletivo, 0.15),
        )
    )


def _midfield_pressing(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("resistencia", attributes.resistencia, 0.25),
            ("aceleracao", attributes.aceleracao, 0.20),
            ("antecipacao", attributes.antecipacao, 0.20),
            ("trabalho_coletivo", attributes.trabalho_coletivo, 0.20),
            ("concentracao", attributes.concentracao, 0.15),
        )
    )


def _attacking_depth(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            (
                "corrida_curta",
                calculate_sprint_ability(profile, SprintContext.SHORT).score,
                0.30,
            ),
            (
                "corrida_longa",
                calculate_sprint_ability(profile, SprintContext.LONG).score,
                0.30,
            ),
            ("posicionamento_ofensivo", attributes.posicionamento_ofensivo, 0.25),
            ("antecipacao", attributes.antecipacao, 0.15),
        )
    )


def _attacking_combination(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("controle", attributes.controle, 0.25),
            ("passe_curto", attributes.passe_curto, 0.25),
            ("decisao", attributes.decisao, 0.20),
            ("visao", attributes.visao, 0.15),
            ("trabalho_coletivo", attributes.trabalho_coletivo, 0.15),
        )
    )


def _attacking_creation(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("drible", attributes.drible, 0.20),
            ("visao", attributes.visao, 0.25),
            ("passe_curto", attributes.passe_curto, 0.15),
            ("cruzamento", attributes.cruzamento, 0.15),
            ("decisao", attributes.decisao, 0.15),
            ("posicionamento_ofensivo", attributes.posicionamento_ofensivo, 0.10),
        )
    )


def _attacking_finishing(profile: PlayerProfile) -> DerivedAbility:
    attributes = profile.attributes
    return derive_weighted_ability(
        (
            ("finalizacao", attributes.finalizacao, 0.35),
            ("compostura", attributes.compostura, 0.25),
            ("potencia_chute", attributes.potencia_chute, 0.15),
            ("posicionamento_ofensivo", attributes.posicionamento_ofensivo, 0.15),
            ("pe_fraco", attributes.pe_fraco, 0.10),
        )
    )
