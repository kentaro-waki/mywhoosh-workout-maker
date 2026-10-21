from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from workout_maker.exporters.zwo import to_zwo
from workout_maker.models import Interval
from workout_maker.presets import make_preset
from workout_maker.storage import to_json


def test_xml_structure_units_and_exact_order(sample):
    payload = to_zwo(sample)
    assert isinstance(payload, bytes)
    assert payload.startswith(b"<?xml version='1.0' encoding='utf-8'?>")
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert b"verify imported intervals and power in the target app" in payload
    root = ET.fromstring(payload)
    assert root.tag == "workout_file"
    assert root.findtext("sportType") == "bike"
    assert root.findtext("name") == sample.name
    assert root.findtext("description") == sample.description
    steps = root.find("workout")
    assert [step.tag for step in steps] == ["SteadyState"] * 3
    assert [step.attrib for step in steps] == [
        {"Duration": "300", "Power": "0.5"},
        {"Duration": "120", "Power": "1"},
        {"Duration": "180", "Power": "0.5"},
    ]


@pytest.mark.parametrize(
    ("percent", "expected"),
    [(0, "0"), (50, "0.5"), (80, "0.8"), (100, "1"), (120, "1.2"), (33.33, "0.3333")],
)
def test_power_is_fraction_not_percent_or_watts(sample, percent, expected):
    workout = replace(sample, intervals=(Interval("target", 15, percent),))
    step = ET.fromstring(to_zwo(workout)).find("workout/SteadyState")
    assert step.get("Duration") == "15"
    assert step.get("Power") == expected


def test_decimal_conversion_does_not_depend_on_context_or_underflow(sample):
    tiny = replace(sample, intervals=(Interval("tiny", 1, 5e-324),))
    with localcontext() as context:
        context.prec = 2
        power = ET.fromstring(to_zwo(tiny)).find("workout/SteadyState").get("Power")
    assert Decimal(power) == Decimal("5e-326")
    assert Decimal(power) > 0
    assert "e" not in power.lower()
    precise = replace(sample, intervals=(Interval("precise", 1, 83.33333333333333),))
    with localcontext() as context:
        context.prec = 2
        power = ET.fromstring(to_zwo(precise)).find("workout/SteadyState").get("Power")
    assert power == "0.8333333333333333"


def test_special_characters_and_whitespace_round_trip(sample):
    name = "A&B <C> \"quoted\" 'single' 日本語 🚲"
    description = "<not-an-element>& text\tline\nnext\rCR\r\nCRLF"
    workout = replace(sample, name=name, description=description)
    payload = to_zwo(workout)
    assert b"&amp;" in payload and b"&lt;" in payload
    assert b"&#13;" in payload
    root = ET.fromstring(payload)
    assert root.findtext("name") == name
    assert root.findtext("description") == description
    assert root.find("not-an-element") is None


@pytest.mark.parametrize("point", [0, 1, 8, 11, 12, 31, 0xFFFE, 0xFFFF])
@pytest.mark.parametrize("field", ["name", "description", "interval_name"])
def test_invalid_xml_characters_are_rejected_not_removed(sample, point, field):
    invalid = "before" + chr(point) + "after"
    if field == "interval_name":
        workout = replace(sample, intervals=(replace(sample.intervals[0], name=invalid),))
    else:
        workout = replace(sample, **{field: invalid})
    with pytest.raises(ValueError, match="unsupported XML 1.0 character"):
        to_zwo(workout)
    assert to_json(workout)  # JSON is still allowed; XML restrictions stay exporter-local.


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("duration_seconds", 0),
        ("duration_seconds", 1.5),
        ("duration_seconds", True),
        ("target_percent", -1),
        ("target_percent", float("nan")),
        ("target_percent", float("inf")),
        ("target_percent", "80"),
    ],
)
def test_export_boundary_revalidates_corrupted_interval(sample, field, value):
    interval = replace(sample.intervals[0])
    object.__setattr__(interval, field, value)
    damaged = replace(sample)
    object.__setattr__(damaged, "intervals", (interval,))
    with pytest.raises(ValueError):
        to_zwo(damaged)


def test_export_boundary_revalidates_workout_and_type(sample):
    damaged = replace(sample)
    object.__setattr__(damaged, "ftp_watts", 0)
    with pytest.raises(ValueError):
        to_zwo(damaged)
    with pytest.raises(ValueError):
        to_zwo({"ftp_watts": 250})


@pytest.mark.parametrize(
    ("key", "count", "seconds"),
    [
        ("4x8", 9, 3360),
        ("30_15", 64, 2610),
        ("sst", 5, 3000),
    ],
)
def test_presets_keep_every_interval_including_final_recoveries(key, count, seconds):
    workout = make_preset(key)
    root = ET.fromstring(to_zwo(workout))
    steps = list(root.find("workout"))
    assert len(steps) == count
    assert root.find(".//IntervalsT") is None
    assert root.find(".//Warmup") is None
    assert root.find(".//Cooldown") is None
    assert all(step.tag == "SteadyState" for step in steps)
    assert sum(int(step.get("Duration")) for step in steps) == seconds
    for step, interval in zip(steps, workout.intervals, strict=True):
        assert int(step.get("Duration")) == interval.duration_seconds
        assert Decimal(step.get("Power")) == Decimal(str(interval.target_percent)) / 100


def test_export_is_deterministic_and_does_not_change_model_or_json(sample):
    before = to_json(sample)
    payload = to_zwo(sample)
    assert to_zwo(sample) == payload
    assert to_json(sample) == before
    assert to_zwo(replace(sample, ftp_watts=300)) == payload


def test_sample_file_has_hand_checkable_values():
    path = Path(__file__).resolve().parents[1] / "examples" / "calculation_sample.zwo"
    root = ET.fromstring(path.read_bytes())
    steps = list(root.find("workout"))
    assert [(s.get("Duration"), s.get("Power")) for s in steps] == [
        ("300", "0.5"),
        ("120", "1"),
        ("180", "0.5"),
    ]
