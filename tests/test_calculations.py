from dataclasses import replace

import pytest

from workout_maker.calculations import format_duration, summarize, timeline
from workout_maker.chart import COLORS, build_figure
from workout_maker.models import Interval


def test_hand_calculated_sample(sample):
    stats = summarize(sample)
    assert stats.duration_seconds == 600
    assert stats.average_watts == 150
    assert stats.work_kj == 90


def test_average_is_weighted_by_duration(sample):
    assert summarize(sample).average_watts != pytest.approx((125 + 250 + 125) / 3)


def test_ftp_change_preserves_percentages_and_time(sample):
    updated = replace(sample, ftp_watts=300)
    assert updated.intervals == sample.intervals
    assert summarize(updated).average_watts == 180
    assert summarize(updated).work_kj == 108


def test_timeline_has_no_gaps_or_overlaps(sample):
    rows = timeline(sample)
    assert [r.start_seconds for r in rows] == [0, 300, 420]
    assert [r.end_seconds for r in rows] == [300, 420, 600]
    assert [r.power_watts for r in rows] == [125, 250, 125]


def test_zero_power_and_fractional_percent_are_not_rounded(sample):
    workout = replace(sample, intervals=(Interval("off", 1, 0), Interval("on", 3, 33.33)))
    assert timeline(workout)[1].power_watts == pytest.approx(83.325)
    assert summarize(workout).work_kj == pytest.approx(0.249975)


def test_bar_geometry_matches_real_time_not_category_spacing(sample):
    figure = build_figure(sample)
    plotted = []
    for trace in figure.data:
        for x, width, y, custom in zip(
            trace.x, trace.width, trace.y, trace.customdata, strict=True
        ):
            plotted.append((custom[3], custom[4], x - width / 2, x + width / 2, y))
    plotted.sort()
    for actual, expected in zip(
        plotted, [(0, 300, 0, 5, 125), (300, 420, 5, 7, 250), (420, 600, 7, 10, 125)], strict=True
    ):
        assert actual == pytest.approx(expected)
    assert figure.layout.xaxis.range == (0, 10)
    assert "経過時間" in figure.layout.xaxis.title.text
    assert "目標出力" in figure.layout.yaxis.title.text


def test_kinds_have_distinct_colors(sample):
    assert len(set(COLORS.values())) == len(COLORS)
    figure = build_figure(sample)
    assert len({trace.marker.color for trace in figure.data}) == 3


@pytest.mark.parametrize(("seconds", "expected"), [(0, "0:00"), (75, "1:15"), (3600, "60:00")])
def test_duration_labels(seconds, expected):
    assert format_duration(seconds) == expected
