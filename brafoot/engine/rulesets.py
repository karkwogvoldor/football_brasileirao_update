"""Versioned configuration for deterministic match simulation rules."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_SEGMENT_DURATION_SECONDS = 3 * 60
DEFAULT_MAX_SUBSTITUTIONS = 5
DEFAULT_MAX_SUBSTITUTION_WINDOWS = 3


@dataclass(frozen=True, slots=True)
class SimulationRuleset:
    """The version and configurable boundaries used by the simulation."""

    version: str
    segment_duration_seconds: int = DEFAULT_SEGMENT_DURATION_SECONDS
    max_substitutions: int = DEFAULT_MAX_SUBSTITUTIONS
    max_substitution_windows: int = DEFAULT_MAX_SUBSTITUTION_WINDOWS
    half_time_substitution_consumes_window: bool = False

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
        if not _is_non_negative_int(self.max_substitutions):
            raise ValueError("O limite de substituições deve ser um inteiro não negativo.")
        if not _is_non_negative_int(self.max_substitution_windows):
            raise ValueError(
                "O limite de janelas de substituição deve ser um inteiro não negativo."
            )
        if not isinstance(self.half_time_substitution_consumes_window, bool):
            raise ValueError(
                "A regra de substituição no intervalo deve ser um valor booleano."
            )


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
