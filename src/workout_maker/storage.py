"""Strict JSON round trips. Never write server-side user files."""

import json
from dataclasses import asdict

from workout_maker.models import MAX_INTERVALS, Interval, Workout

MAX_JSON_BYTES = 1024 * 1024  # Application guard, unrelated to MyWhoosh limits.


def to_json(workout: Workout) -> str:
    data = {"schema_version": 1, **asdict(workout)}
    text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if len(text.encode("utf-8")) > MAX_JSON_BYTES:
        raise ValueError("JSON file is larger than 1 MiB; shorten names or descriptions")
    return text


def _object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON number: {value}")


def _keys(data: object, required: set[str], optional: set[str], name: str) -> dict:
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be an object")
    missing = required - data.keys()
    extra = data.keys() - required - optional
    if missing or extra:
        raise ValueError(f"{name}: missing={sorted(missing)}, unsupported={sorted(extra)}")
    return data


def from_json(payload: str | bytes) -> Workout:
    """Validate fully before replacing the current UI workout."""
    try:
        if isinstance(payload, bytes):
            if len(payload) > MAX_JSON_BYTES:
                raise ValueError("JSON file is larger than 1 MiB")
            text = payload.decode("utf-8-sig")
        elif isinstance(payload, str):
            if len(payload.encode("utf-8")) > MAX_JSON_BYTES:
                raise ValueError("JSON file is larger than 1 MiB")
            text = payload.removeprefix("\ufeff")
        else:
            raise ValueError("JSON input must be text or bytes")
        data = json.loads(text, object_pairs_hook=_object, parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid UTF-8 JSON") from exc
    data = _keys(
        data, {"schema_version", "name", "ftp_watts", "intervals"}, {"description"}, "workout"
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported schema_version (expected integer 1)")
    rows = data["intervals"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_INTERVALS:
        raise ValueError(f"intervals must be an array of 1..{MAX_INTERVALS} items")
    intervals = []
    for row in rows:
        row = _keys(row, {"name", "duration_seconds", "target_percent"}, {"kind"}, "interval")
        intervals.append(Interval(**row))
    return Workout(
        name=data["name"],
        ftp_watts=data["ftp_watts"],
        intervals=tuple(intervals),
        description=data.get("description", ""),
    )
