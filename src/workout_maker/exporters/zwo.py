"""Experimental steady-state ZWO serialization; target-app behavior must be checked.

No network or filesystem access. Individual interval names and kind/color metadata
are not represented by this minimal subset; keep the original JSON for editing.
"""

from dataclasses import replace
from decimal import Decimal
from xml.etree import ElementTree as ET

from workout_maker.models import Interval, Workout


def _validate_xml_text(value: str, field: str) -> None:
    """Reject characters forbidden in XML 1.0 rather than deleting them."""
    for character in value:
        point = ord(character)
        if not (
            point in (0x9, 0xA, 0xD)
            or 0x20 <= point <= 0xD7FF
            or 0xE000 <= point <= 0xFFFD
            or 0x10000 <= point <= 0x10FFFF
        ):
            raise ValueError(f"{field} contains an unsupported XML 1.0 character U+{point:04X}")


def _power_ratio(percent: int | float) -> str:
    """Divide the canonical decimal spelling by 100 without rounding/underflow.

    Constructing a Decimal tuple changes its exponent exactly, independently of the
    active Decimal context precision. Formatting as fixed point avoids exponent syntax.
    """
    parts = Decimal(str(percent)).as_tuple()
    ratio = Decimal((parts.sign, parts.digits, parts.exponent - 2))
    if ratio.is_zero():
        return "0"
    value = format(ratio, "f")
    return value.rstrip("0").rstrip(".") if "." in value else value


def to_zwo(workout: Workout) -> bytes:
    """Return deterministic UTF-8 XML with one SteadyState per input interval.

    The Workout and Interval models are not changed. Reconstruct validated snapshots
    at this boundary so invalid/externally corrupted dataclass values are rejected.
    Power contains an FTP fraction, never absolute watts. FTP itself is not embedded.
    The receiver decides which FTP to apply; the resulting targets must be checked.
    """
    if not isinstance(workout, Workout):
        raise ValueError("ZWO export requires a Workout")
    if not isinstance(workout.intervals, tuple) or not all(
        isinstance(item, Interval) for item in workout.intervals
    ):
        raise ValueError("ZWO export requires a tuple of Interval objects")
    validated = replace(workout, intervals=tuple(replace(item) for item in workout.intervals))
    _validate_xml_text(validated.name, "workout name")
    _validate_xml_text(validated.description, "description")
    for index, item in enumerate(validated.intervals):
        _validate_xml_text(item.name, f"interval {index + 1} name")

    root = ET.Element("workout_file")
    root.append(
        ET.Comment(
            "Experimental ZWO export; verify imported intervals and power in the target app."
        )
    )
    ET.SubElement(root, "author").text = "Workout Maker"
    ET.SubElement(root, "name").text = validated.name
    ET.SubElement(root, "description").text = validated.description
    ET.SubElement(root, "sportType").text = "bike"
    ET.SubElement(root, "tags")
    steps = ET.SubElement(root, "workout")
    for item in validated.intervals:
        ET.SubElement(
            steps,
            "SteadyState",
            {"Duration": str(item.duration_seconds), "Power": _power_ratio(item.target_percent)},
        )
    ET.indent(root, space="  ")
    payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    # XML parsers normalize literal carriage returns; character references preserve
    # valid CR/CRLF in metadata exactly, including CR from uploaded JSON strings.
    return payload.replace(b"\r", b"&#13;") + b"\n"
