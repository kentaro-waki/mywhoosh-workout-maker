"""Numeric time coordinates and explicit widths, rather than categorical bars."""

from html import escape

import plotly.graph_objects as go

from workout_maker.calculations import timeline
from workout_maker.models import KIND_LABELS, KINDS, Workout

COLORS = {
    "warmup": "#38bdf8",
    "work": "#f97316",
    "recovery": "#34d399",
    "cooldown": "#818cf8",
    "steady": "#eab308",
}


def build_figure(workout: Workout) -> go.Figure:
    rows = timeline(workout)
    figure = go.Figure()
    for kind in KINDS:
        selected = [row for row in rows if row.kind == kind]
        if not selected:
            continue
        figure.add_trace(
            go.Bar(
                name=KIND_LABELS[kind],
                x=[(row.start_seconds + row.duration_seconds / 2) / 60 for row in selected],
                y=[row.power_watts for row in selected],
                width=[row.duration_seconds / 60 for row in selected],
                marker_color=COLORS[kind],
                marker_line_width=0,
                customdata=[
                    [
                        escape(row.name),
                        row.target_percent,
                        row.duration_seconds,
                        row.start_seconds,
                        row.end_seconds,
                    ]
                    for row in selected
                ],
                hovertemplate=(
                    "%{customdata[0]}<br>%{y:.1f} W / %{customdata[1]}% FTP"
                    "<br>%{customdata[2]} 秒<extra>%{fullData.name}</extra>"
                ),
            )
        )
    figure.add_hline(
        y=workout.ftp_watts,
        line_dash="dot",
        line_color="#64748b",
        annotation_text="FTP",
        annotation_position="top right",
    )
    figure.update_layout(
        template="plotly_white",
        barmode="overlay",
        bargap=0,
        height=380,
        xaxis_title="経過時間（分）",
        yaxis_title="目標出力（W）",
        xaxis_range=[0, rows[-1].end_seconds / 60],
        yaxis_rangemode="tozero",
        legend={"orientation": "h", "y": 1.15},
        margin={"l": 30, "r": 20, "t": 50, "b": 40},
    )
    return figure
