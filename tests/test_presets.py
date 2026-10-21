from dataclasses import replace

import pytest

from workout_maker.calculations import summarize
from workout_maker.editing import update_interval
from workout_maker.presets import make_preset
from workout_maker.storage import from_json, to_json


@pytest.mark.parametrize(
    ("key", "count", "seconds", "work_count"),
    [
        ("4x8", 9, 3360, 4),
        ("30_15", 64, 2610, 30),
        ("sst", 5, 3000, 2),
    ],
)
def test_preset_structure_and_duration(key, count, seconds, work_count):
    workout = make_preset(key)
    assert len(workout.intervals) == count
    assert summarize(workout).duration_seconds == seconds
    assert sum(i.kind == "work" for i in workout.intervals) == work_count
    assert workout.intervals[0].kind == "warmup"
    assert workout.intervals[-1].kind == "cooldown"
    assert from_json(to_json(workout)) == workout
    assert "最適性" in workout.description


@pytest.mark.parametrize("key", ["4x8", "30_15", "sst"])
def test_preset_time_and_intensity_are_editable_without_changing_factory(key):
    workout = make_preset(key)
    modified = update_interval(
        workout, 1, replace(workout.intervals[1], duration_seconds=42, target_percent=87.5)
    )
    assert modified.intervals[1].duration_seconds == 42
    assert modified.intervals[1].target_percent == 87.5
    assert make_preset(key) == workout
