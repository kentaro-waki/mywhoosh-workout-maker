import pytest

from workout_maker.models import Interval, Workout


@pytest.fixture
def sample():
    return Workout(
        "計算例",
        250,
        (
            Interval("A", 300, 50, "warmup"),
            Interval("B", 120, 100, "work"),
            Interval("C", 180, 50, "recovery"),
        ),
        "検証用の合成データ",
    )
