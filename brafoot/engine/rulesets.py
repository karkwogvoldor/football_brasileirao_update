"""Versioned configuration for deterministic match simulation rules."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_SEGMENT_DURATION_SECONDS = 3 * 60
DEFAULT_MAX_SUBSTITUTIONS = 5
DEFAULT_MAX_SUBSTITUTION_WINDOWS = 3


@dataclass(frozen=True, slots=True)
class SimulationTuning:
    """Calibrable probabilities and durations of event generation.

    Ratings are normalized to ``[0, 1]`` before use, so every slope is the change
    in probability for a full-scale advantage. Changing a value changes match
    behavior and therefore requires a new ruleset version.
    """

    home_edge: float = 0.02
    pass_base: float = 0.86
    pass_slope: float = 0.12
    pass_skill_slope: float = 0.12
    forward_pass_penalty: float = 0.06
    attacking_pass_penalty: float = 0.05
    pass_success_min: float = 0.55
    pass_success_max: float = 0.95
    forward_pass_share: float = 0.34
    backward_pass_share: float = 0.10
    carry_base: float = 0.76
    carry_slope: float = 0.2
    carry_skill_slope: float = 0.18
    carry_forward_share: float = 0.50
    cross_base: float = 0.34
    cross_slope: float = 0.2
    cross_skill_slope: float = 0.18
    cross_header_share: float = 0.5
    cross_weight: float = 0.2
    shot_weight_center: float = 0.14
    shot_weight_wide: float = 0.05
    shot_off_target: float = 0.36
    shot_blocked: float = 0.28
    shot_skill_slope: float = 0.2
    goal_given_on_target: float = 0.30
    goal_skill_slope: float = 0.3
    goal_min: float = 0.10
    goal_max: float = 0.65
    wide_shot_goal_factor: float = 0.60
    pass_seconds: tuple[int, int] = (7, 13)
    carry_seconds: tuple[int, int] = (6, 11)
    cross_seconds: tuple[int, int] = (8, 12)
    shot_seconds: tuple[int, int] = (6, 10)
    goal_dead_time_seconds: int = 45


@dataclass(frozen=True, slots=True)
class SimulationRuleset:
    """The version and configurable boundaries used by the simulation."""

    version: str
    segment_duration_seconds: int = DEFAULT_SEGMENT_DURATION_SECONDS
    max_substitutions: int = DEFAULT_MAX_SUBSTITUTIONS
    max_substitution_windows: int = DEFAULT_MAX_SUBSTITUTION_WINDOWS
    half_time_substitution_consumes_window: bool = False
    tuning: SimulationTuning = SimulationTuning()

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
        if not isinstance(self.tuning, SimulationTuning):
            raise ValueError("A calibração da simulação não é válida.")


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
