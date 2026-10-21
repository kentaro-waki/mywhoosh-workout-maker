"""Immutable interval operations shared by UI and tests."""

from dataclasses import replace

from workout_maker.models import Interval, Workout


def _check_index(workout: Workout, index: int) -> None:
    if type(index) is not int or not 0 <= index < len(workout.intervals):
        raise ValueError("interval index is out of range")


def update_interval(workout: Workout, index: int, interval: Interval) -> Workout:
    _check_index(workout, index)
    rows = list(workout.intervals)
    rows[index] = interval
    return replace(workout, intervals=tuple(rows))


def insert_after(workout: Workout, index: int, interval: Interval) -> Workout:
    _check_index(workout, index)
    rows = list(workout.intervals)
    rows.insert(index + 1, interval)
    return replace(workout, intervals=tuple(rows))


def duplicate_interval(workout: Workout, index: int) -> Workout:
    _check_index(workout, index)
    item = replace(workout.intervals[index], name=workout.intervals[index].name[:193] + " (copy)")
    return insert_after(workout, index, item)


def delete_interval(workout: Workout, index: int) -> Workout:
    _check_index(workout, index)
    if len(workout.intervals) == 1:
        raise ValueError("the last interval cannot be deleted")
    return replace(workout, intervals=workout.intervals[:index] + workout.intervals[index + 1 :])


def move_interval(workout: Workout, index: int, offset: int) -> Workout:
    _check_index(workout, index)
    if type(offset) is not int or offset not in (-1, 1):
        raise ValueError("offset must be -1 or +1")
    _check_index(workout, index + offset)
    rows = list(workout.intervals)
    rows[index], rows[index + offset] = rows[index + offset], rows[index]
    return replace(workout, intervals=tuple(rows))
