"""Validated, immutable workout definitions; percentage is the source of truth."""

import math
from dataclasses import dataclass

KINDS = ("warmup", "work", "recovery", "cooldown", "steady")
KIND_LABELS = {
    "warmup": "ウォームアップ",
    "work": "高強度・主区間",
    "recovery": "回復",
    "cooldown": "クールダウン",
    "steady": "定常走",
}
MAX_INTERVALS = 1000  # Application guard; not a MyWhoosh specification.
MAX_DURATION_SECONDS = 7 * 24 * 3600  # Per interval; an application guard only.


def finite_number(value: object, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} is too large") from exc
    if not math.isfinite(result) or (result <= 0 if positive else result < 0):
        sign = "positive" if positive else "non-negative"
        raise ValueError(f"{name} must be finite and {sign}")
    return result


def valid_text(
    value: object, name: str, *, allow_empty: bool = False, max_length: int = 200
) -> None:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValueError(f"{name} must be a {'possibly empty ' if allow_empty else ''}string")
    if len(value) > max_length:
        raise ValueError(f"{name} is too long (maximum {max_length} characters)")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{name} must be valid UTF-8 text") from exc


@dataclass(frozen=True)
class Interval:
    name: str
    duration_seconds: int
    target_percent: float
    kind: str = "steady"

    def __post_init__(self) -> None:
        valid_text(self.name, "interval name")
        if (
            type(self.duration_seconds) is not int
            or not 1 <= self.duration_seconds <= MAX_DURATION_SECONDS
        ):
            raise ValueError("duration_seconds must be an integer from 1 to 604800")
        finite_number(self.target_percent, "target_percent")
        if self.kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")


@dataclass(frozen=True)
class Workout:
    name: str
    ftp_watts: float
    intervals: tuple[Interval, ...]
    description: str = ""

    def __post_init__(self) -> None:
        valid_text(self.name, "workout name")
        valid_text(self.description, "description", allow_empty=True, max_length=10000)
        ftp = finite_number(self.ftp_watts, "ftp_watts", positive=True)
        if not isinstance(self.intervals, tuple) or not 1 <= len(self.intervals) <= MAX_INTERVALS:
            raise ValueError(f"intervals must be a tuple of 1..{MAX_INTERVALS} intervals")
        for item in self.intervals:
            if not isinstance(item, Interval):
                raise ValueError("intervals must contain Interval objects")
            power = ftp * (float(item.target_percent) / 100)
            if not math.isfinite(power) or not math.isfinite(power * item.duration_seconds):
                raise ValueError("derived power or work is too large")
        if not math.isfinite(
            sum(ftp * (i.target_percent / 100) * i.duration_seconds for i in self.intervals)
        ):
            raise ValueError("total work is too large")
