import json
from dataclasses import replace

import pytest

from workout_maker.models import Interval
from workout_maker.storage import from_json, to_json


def test_round_trip_preserves_japanese_and_all_fields(sample):
    text = to_json(sample)
    assert "計算例" in text
    assert from_json(text) == sample
    assert from_json(text.encode("utf-8")) == sample
    assert from_json(b"\xef\xbb\xbf" + text.encode("utf-8")) == sample


def test_file_format_is_versioned_and_percent_based(sample):
    data = json.loads(to_json(sample))
    assert data["schema_version"] == 1
    assert data["intervals"][1]["target_percent"] == 100
    assert "power_watts" not in data["intervals"][1]


@pytest.mark.parametrize("ftp", [0, -1, True, "250", None, float("nan"), float("inf")])
def test_invalid_ftp_is_rejected(sample, ftp):
    data = json.loads(to_json(sample))
    data["ftp_watts"] = ftp
    with pytest.raises(ValueError):
        from_json(json.dumps(data))


@pytest.mark.parametrize("duration", [0, -1, 1.5, True, "60", 604801])
def test_invalid_duration_is_rejected(duration):
    with pytest.raises(ValueError):
        Interval("bad", duration, 50)


@pytest.mark.parametrize("percent", [-1, True, "50", float("nan"), float("inf")])
def test_invalid_percentage_is_rejected(percent):
    with pytest.raises(ValueError):
        Interval("bad", 60, percent)


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        "null",
        '{"schema_version":1,"schema_version":1}',
        '{"number":NaN}',
        "[",
        b"\xff",
        "[" * 2000,
    ],
)
def test_malformed_json_is_rejected(payload):
    with pytest.raises(ValueError):
        from_json(payload)


@pytest.mark.parametrize("version", [2, True, 1.0, "1"])
def test_unknown_or_wrongly_typed_version_is_rejected(sample, version):
    data = json.loads(to_json(sample))
    data["schema_version"] = version
    with pytest.raises(ValueError, match="schema_version"):
        from_json(json.dumps(data))


def test_unknown_fields_are_not_silently_discarded(sample):
    data = json.loads(to_json(sample))
    data["cadence"] = 90
    with pytest.raises(ValueError, match="unsupported"):
        from_json(json.dumps(data))


def test_empty_workout_and_resource_limit(sample):
    data = json.loads(to_json(sample))
    data["intervals"] = []
    with pytest.raises(ValueError):
        from_json(json.dumps(data))
    with pytest.raises(ValueError, match="1 MiB"):
        from_json(" " * (1024 * 1024 + 1))


def test_overflowing_derived_values_are_rejected(sample):
    with pytest.raises(ValueError, match="too large"):
        replace(sample, ftp_watts=1e308)


def test_optional_description_and_kind_have_explicit_defaults(sample):
    data = json.loads(to_json(sample))
    del data["description"]
    del data["intervals"][0]["kind"]
    loaded = from_json(json.dumps(data))
    assert loaded.description == ""
    assert loaded.intervals[0].kind == "steady"


def test_invalid_unicode_and_overlong_name_are_rejected():
    with pytest.raises(ValueError, match="UTF-8"):
        Interval("\ud800", 60, 50)
    with pytest.raises(ValueError, match="too long"):
        Interval("a" * 201, 60, 50)


def test_save_does_not_create_a_file_that_exceeds_load_limit(sample):
    large = replace(sample, intervals=(Interval("\x01" * 200, 60, 50),) * 1000)
    with pytest.raises(ValueError, match="1 MiB"):
        to_json(large)
