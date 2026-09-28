"""Enumerate the (rung x angle x sample) cells for one model."""
from collections.abc import Iterator
from dataclasses import dataclass

from trolley.angles import ANGLES, Angle
from trolley.scenarios import RUNGS, Rung

DEFAULT_SAMPLES = 4
# Jev is deterministic; two samples cover both option orders and nothing more
# is learned by repeating. See spec section 2.1.
SAMPLES_BY_MODEL = {"jev": 2}


def samples_for(model_key: str) -> int:
    return SAMPLES_BY_MODEL.get(model_key, DEFAULT_SAMPLES)


@dataclass(frozen=True)
class Cell:
    model_key: str
    rung: Rung
    angle: Angle
    sample_idx: int
    option_a_is_act: bool


def cells_for_model(model_key: str, samples: int = DEFAULT_SAMPLES) -> Iterator[Cell]:
    if samples % 2 != 0:
        raise ValueError(
            f"samples must be even so option order balances; got {samples}"
        )
    for rung in RUNGS:
        for angle in ANGLES:
            for i in range(samples):
                yield Cell(model_key, rung, angle, i, option_a_is_act=(i % 2 == 0))
