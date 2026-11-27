"""Reproducible, platform-independent random draws for match simulation.

A draw depends only on the seed and the draw position, so a persisted
``(random_seed, random_step)`` pair is enough to resume a match exactly.
"""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import blake2b
from typing import TypeVar

T = TypeVar("T")

_UNIT = float(1 << 64)


class DeterministicStream:
    """A counter-based stream: draw ``n`` is a pure function of ``(seed, n)``."""

    __slots__ = ("_seed", "_step")

    def __init__(self, seed: int, step: int = 0) -> None:
        if not _is_non_negative_int(seed) or not _is_non_negative_int(step):
            raise ValueError("A semente e a posição do gerador devem ser não negativas.")
        self._seed = seed
        self._step = step

    @property
    def step(self) -> int:
        """The number of draws already consumed from the seed."""

        return self._step

    def random(self) -> float:
        """Return the next draw in ``[0, 1)``."""

        digest = blake2b(
            f"{self._seed}:{self._step}".encode("ascii"), digest_size=8
        ).digest()
        self._step += 1
        return int.from_bytes(digest, "big") / _UNIT

    def between(self, low: int, high: int) -> int:
        """Return an integer in ``[low, high]``."""

        if high < low:
            raise ValueError("O intervalo sorteado é inválido.")
        return low + int(self.random() * (high - low + 1))

    def chance(self, probability: float) -> bool:
        """Return ``True`` with the given probability (clamped to ``[0, 1]``)."""

        return self.random() < min(max(probability, 0.0), 1.0)

    def choose(self, items: Sequence[T], weights: Sequence[float]) -> T:
        """Pick one item proportionally to non-negative weights."""

        if not items or len(items) != len(weights):
            raise ValueError("Os itens e pesos sorteados não são válidos.")
        total = sum(weights)
        if total <= 0 or any(weight < 0 for weight in weights):
            raise ValueError("Os pesos do sorteio devem ser não negativos e somar mais que zero.")
        target = self.random() * total
        cumulative = 0.0
        for item, weight in zip(items, weights):
            cumulative += weight
            if target < cumulative:
                return item
        return items[-1]


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
