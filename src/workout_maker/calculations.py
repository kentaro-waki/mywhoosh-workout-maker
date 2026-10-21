"""Pure calculations. Seconds, watts, and mechanical kilojoules."""

from dataclasses import dataclass

from workout_maker.models import Workout


@dataclass(frozen=True)
class Segment:
    index: int
    name: str
    kind: str
    start_seconds: int
    duration_seconds: int
    target_percent: float
    power_watts: float

    @property
    def end_seconds(self) -> int:
        return self.start_seconds + self.duration_seconds


@dataclass(frozen=True)
class Summary:
    duration_seconds: int
    average_watts: float
    work_kj: float


def timeline(workout: Workout) -> tuple[Segment, ...]:
    """Return contiguous intervals without resampling or rounding target powers."""
    rows = []
    start = 0
    for index, item in enumerate(workout.intervals):
        rows.append(
            Segment(
                index,
                item.name,
                item.kind,
                start,
                item.duration_seconds,
                item.target_percent,
                workout.ftp_watts * (item.target_percent / 100),
            )
        )
        start += item.duration_seconds
    return tuple(rows)


def summarize(workout: Workout) -> Summary:
    rows = timeline(workout)
    seconds = sum(row.duration_seconds for row in rows)
    joules = sum(row.power_watts * row.duration_seconds for row in rows)
    return Summary(seconds, joules / seconds, joules / 1000)


def format_duration(seconds: int) -> str:
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}:{remainder:02d}"
