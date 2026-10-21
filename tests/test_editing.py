from dataclasses import FrozenInstanceError, replace

import pytest

from workout_maker.editing import (
    delete_interval,
    duplicate_interval,
    insert_after,
    move_interval,
    update_interval,
)
from workout_maker.models import Interval


def test_edit_changes_only_selected_interval(sample):
    new = Interval("edited", 30, 120, "work")
    updated = update_interval(sample, 1, new)
    assert updated.intervals == (sample.intervals[0], new, sample.intervals[2])
    assert sample.intervals[1].duration_seconds == 120


def test_insert_and_duplicate(sample):
    new = Interval("new", 15, 40, "recovery")
    inserted = insert_after(sample, 0, new)
    assert inserted.intervals == (sample.intervals[0], new, *sample.intervals[1:])
    copied = duplicate_interval(sample, 1)
    assert len(copied.intervals) == 4
    assert copied.intervals[2] == replace(sample.intervals[1], name="B (copy)")


def test_delete_and_reorder_preserve_remaining_values(sample):
    moved = move_interval(sample, 1, -1)
    assert moved.intervals == (sample.intervals[1], sample.intervals[0], sample.intervals[2])
    assert move_interval(moved, 0, 1) == sample
    assert delete_interval(sample, 1).intervals == (sample.intervals[0], sample.intervals[2])


@pytest.mark.parametrize(("index", "offset"), [(0, -1), (2, 1), (1, 2), (-1, 1), (True, 1)])
def test_invalid_move_does_not_change_workout(sample, index, offset):
    original = sample.intervals
    with pytest.raises(ValueError):
        move_interval(sample, index, offset)
    assert sample.intervals == original


def test_last_interval_cannot_be_deleted(sample):
    with pytest.raises(ValueError, match="last interval"):
        delete_interval(replace(sample, intervals=(sample.intervals[0],)), 0)


def test_model_is_immutable(sample):
    with pytest.raises(FrozenInstanceError):
        sample.ftp_watts = 300


def test_duplicate_handles_maximum_length_name(sample):
    workout = update_interval(sample, 0, replace(sample.intervals[0], name="a" * 200))
    copied = duplicate_interval(workout, 0)
    assert len(copied.intervals[1].name) == 200
    assert copied.intervals[1].name.endswith(" (copy)")
