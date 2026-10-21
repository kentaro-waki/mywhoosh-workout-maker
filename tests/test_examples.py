from pathlib import Path

import pytest

from workout_maker.calculations import summarize
from workout_maker.presets import make_preset
from workout_maker.storage import from_json

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize("key", ["4x8", "30_15", "sst"])
def test_distributed_presets_match_factory(key):
    assert from_json((EXAMPLES / f"{key}.json").read_bytes()) == make_preset(key)


def test_distributed_calculation_example():
    example = from_json((EXAMPLES / "calculation_sample.json").read_bytes())
    summary = summarize(example)
    assert (summary.duration_seconds, summary.average_watts, summary.work_kj) == (600, 150, 90)
