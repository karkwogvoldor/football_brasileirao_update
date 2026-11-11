import pytest

from brafoot.engine.rulesets import (
    DEFAULT_SEGMENT_DURATION_SECONDS,
    SimulationRuleset,
)


# Usa segmentos de três minutos como configuração regulamentar inicial.
def test_simulation_ruleset_uses_default_segment_duration():
    ruleset = SimulationRuleset(version="2026.1")

    assert ruleset.version == "2026.1"
    assert ruleset.segment_duration_seconds == 180
    assert ruleset.segment_duration_seconds == DEFAULT_SEGMENT_DURATION_SECONDS


# Permite reduzir a duração do segmento sem alterar a versão informada.
def test_simulation_ruleset_accepts_custom_segment_duration():
    ruleset = SimulationRuleset(
        version="2026.1-fast",
        segment_duration_seconds=60,
    )

    assert ruleset.version == "2026.1-fast"
    assert ruleset.segment_duration_seconds == 60


# Rejeita versões vazias ou com espaços externos que gerariam identidades ambíguas.
@pytest.mark.parametrize("version", ["", "   ", " 2026.1", "2026.1 "])
def test_simulation_ruleset_requires_canonical_version(version):
    with pytest.raises(ValueError, match="versão"):
        SimulationRuleset(version=version)


# Rejeita durações que não representam segundos inteiros positivos.
@pytest.mark.parametrize("duration", [0, -1, True, 1.5])
def test_simulation_ruleset_requires_positive_integer_segment_duration(duration):
    with pytest.raises(ValueError, match="duração"):
        SimulationRuleset(
            version="2026.1",
            segment_duration_seconds=duration,
        )
