"""Versioned configuration for deterministic match simulation rules."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_SEGMENT_DURATION_SECONDS = 3 * 60


@dataclass(frozen=True, slots=True)
class SimulationRuleset:
    """The version and configurable boundaries used by the simulation."""

    version: str
    segment_duration_seconds: int = DEFAULT_SEGMENT_DURATION_SECONDS

    def __post_init__(self) -> None:
        if (
            not isinstance(self.version, str)
            or not self.version
            or self.version.strip() != self.version
        ):
            raise ValueError("A versão do conjunto de regras não é válida.")
        if (
            not isinstance(self.segment_duration_seconds, int)
            or isinstance(self.segment_duration_seconds, bool)
            or self.segment_duration_seconds <= 0
        ):
            raise ValueError("A duração do segmento deve ser um inteiro positivo.")
