"""Immutable state and checkpoint types for segmented match simulation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from brafoot.engine.clock import MatchClock, MatchPeriod
from brafoot.engine.matches import MatchSide
from brafoot.engine.rulesets import SimulationRuleset
from brafoot.engine.zones import FieldLane, FieldThird, FieldZone


KICKOFF_ZONE = FieldZone(FieldThird.MIDDLE, FieldLane.CENTER)


@dataclass(frozen=True, slots=True)
class MatchState:
    """The currently implemented deterministic core of a match state."""

    clock: MatchClock
    home_score: int
    away_score: int
    possession: MatchSide
    ball_zone: FieldZone
    ruleset_version: str
    random_seed: int
    random_step: int

    def __post_init__(self) -> None:
        if not isinstance(self.clock, MatchClock):
            raise ValueError("O relógio do estado da partida não é válido.")
        if not _is_non_negative_int(self.home_score) or not _is_non_negative_int(
            self.away_score
        ):
            raise ValueError("O placar deve conter números inteiros não negativos.")
        if not isinstance(self.possession, MatchSide):
            raise ValueError("O lado com a posse da bola não é válido.")
        if not isinstance(self.ball_zone, FieldZone):
            raise ValueError("A zona da bola não é válida.")
        if not _is_canonical_version(self.ruleset_version):
            raise ValueError("A versão do conjunto de regras não é válida.")
        if not _is_non_negative_int(self.random_seed):
            raise ValueError("A semente da simulação deve ser um inteiro não negativo.")
        if not _is_non_negative_int(self.random_step):
            raise ValueError("A posição do gerador deve ser um inteiro não negativo.")

    @classmethod
    def start(
        cls,
        *,
        ruleset: SimulationRuleset,
        kickoff_side: MatchSide,
        random_seed: int,
    ) -> MatchState:
        """Create the deterministic core state at the opening kickoff."""

        if not isinstance(ruleset, SimulationRuleset):
            raise ValueError("O conjunto de regras da partida não é válido.")
        return cls(
            clock=MatchClock.start(),
            home_score=0,
            away_score=0,
            possession=kickoff_side,
            ball_zone=KICKOFF_ZONE,
            ruleset_version=ruleset.version,
            random_seed=random_seed,
            random_step=0,
        )

    def to_snapshot(self) -> dict[str, object]:
        """Return an explicit persistence representation of this state."""

        return {
            "elapsed_seconds": self.clock.elapsed_seconds,
            "period": self.clock.period.value,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "possession": self.possession.value,
            "ball_zone": self.ball_zone.code,
            "ruleset_version": self.ruleset_version,
            "random_seed": self.random_seed,
            "random_step": self.random_step,
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, object]) -> MatchState:
        """Restore and validate a state from its persistence representation."""

        if not isinstance(snapshot, Mapping):
            raise ValueError("O snapshot do estado da partida não é válido.")
        try:
            return cls(
                clock=MatchClock(
                    elapsed_seconds=snapshot["elapsed_seconds"],
                    period=MatchPeriod(snapshot["period"]),
                ),
                home_score=snapshot["home_score"],
                away_score=snapshot["away_score"],
                possession=MatchSide(snapshot["possession"]),
                ball_zone=FieldZone.from_code(snapshot["ball_zone"]),
                ruleset_version=snapshot["ruleset_version"],
                random_seed=snapshot["random_seed"],
                random_step=snapshot["random_step"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("O snapshot do estado da partida não é válido.") from error


@dataclass(frozen=True, slots=True)
class MatchCheckpoint:
    """A sequenced, persistable snapshot boundary between match segments."""

    sequence: int
    state: MatchState

    def __post_init__(self) -> None:
        if not _is_non_negative_int(self.sequence):
            raise ValueError("A sequência do checkpoint deve ser não negativa.")
        if not isinstance(self.state, MatchState):
            raise ValueError("O estado do checkpoint não é válido.")

    def to_snapshot(self) -> dict[str, object]:
        """Return an explicit persistence representation of this checkpoint."""

        return {
            "sequence": self.sequence,
            "state": self.state.to_snapshot(),
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, object]) -> MatchCheckpoint:
        """Restore and validate a checkpoint from its persisted snapshot."""

        if not isinstance(snapshot, Mapping):
            raise ValueError("O snapshot do checkpoint não é válido.")
        try:
            state_snapshot = snapshot["state"]
            if not isinstance(state_snapshot, Mapping):
                raise ValueError("O estado persistido não é válido.")
            return cls(
                sequence=snapshot["sequence"],
                state=MatchState.from_snapshot(state_snapshot),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("O snapshot do checkpoint não é válido.") from error


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_canonical_version(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value
