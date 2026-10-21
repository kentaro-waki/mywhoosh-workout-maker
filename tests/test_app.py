from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from workout_maker.presets import make_preset
from workout_maker.storage import to_json

APP = Path(__file__).resolve().parents[1] / "app.py"


def element_by_label(elements, label):
    return next(item for item in elements if item.label == label)


def start():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    return app


def test_initial_screen_and_ftp_change():
    app = start()
    assert app.metric[0].value == "56:00"
    assert len(app.get("plotly_chart")) == 1
    original = app.session_state["workout"]
    app.number_input(key="ftp_0").set_value(300).run()
    assert not app.exception
    assert app.session_state["workout"].ftp_watts == 300
    assert app.session_state["workout"].intervals == original.intervals


@pytest.mark.parametrize(("key", "time"), [("30_15", "43:30"), ("sst", "50:00")])
def test_loading_presets_updates_screen(key, time):
    app = start()
    app.selectbox(key="preset_choice").select(key).run()
    app.button(key="load_preset").click().run()
    assert not app.exception
    assert app.metric[0].value == time


def test_interval_edit_duplicate_move_delete_and_add():
    app = start()
    element_by_label(app.number_input, "時間（分）").set_value(1)
    element_by_label(app.number_input, "時間（秒）").set_value(15)
    element_by_label(app.number_input, "目標（%FTP）").set_value(75)
    element_by_label(app.button, "区間の変更を適用").click().run()
    assert not app.exception
    assert app.session_state["workout"].intervals[0].duration_seconds == 75
    assert app.session_state["workout"].intervals[0].target_percent == 75
    app.button(key="duplicate_interval").click().run()
    assert len(app.session_state["workout"].intervals) == 10
    app.button(key="move_down").click().run()
    assert app.session_state["workout"].intervals[2].name.endswith("(copy)")
    app.button(key="delete_interval").click().run()
    assert len(app.session_state["workout"].intervals) == 9
    app.button(key="add_interval").click().run()
    assert app.session_state["workout"].intervals[3].name == "新しい区間"
    assert not app.exception


def test_bad_json_keeps_current_edit_and_valid_json_replaces_it():
    app = start()
    before = app.session_state["workout"]
    app.text_area(key="json_text").set_value("invalid json").run()
    app.button(key="load_text").click().run()
    assert not app.exception
    assert app.error
    assert app.session_state["workout"] == before
    app.text_area(key="json_text").set_value(to_json(make_preset("sst", 175))).run()
    app.button(key="load_text").click().run()
    assert not app.exception
    assert app.session_state["workout"] == make_preset("sst", 175)
    assert app.number_input(key="ftp_1").value == 175


def test_invalid_interval_does_not_replace_applied_data():
    app = start()
    before = app.session_state["workout"]
    element_by_label(app.number_input, "時間（分）").set_value(0)
    element_by_label(app.number_input, "時間（秒）").set_value(0)
    element_by_label(app.button, "区間の変更を適用").click().run()
    assert not app.exception
    assert app.error
    assert app.session_state["workout"] == before
