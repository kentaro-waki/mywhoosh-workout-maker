from dataclasses import replace
from pathlib import Path

from streamlit.testing.v1 import AppTest

from workout_maker.presets import make_preset
from workout_maker.storage import from_json, to_json

APP = Path(__file__).resolve().parents[1] / "app.py"


def downloads(app):
    return {item.proto.id.rsplit("-", 1)[-1]: item.proto for item in app.get("download_button")}


def test_zwo_and_json_downloads_show_reported_verification_scope():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    buttons = downloads(app)
    assert set(buttons) == {"download_json", "download_zwo"}
    assert not buttons["download_zwo"].disabled
    assert not buttons["download_json"].disabled
    assert buttons["download_zwo"].label == "ZWOをダウンロード（試験）"
    assert buttons["download_zwo"].url
    warnings = "".join(item.value for item in app.warning)
    assert "区間数・合計時間の一致をユーザーが確認" in warnings
    assert "アプリへの同期、実走時の出力制御、他環境は未検証" in warnings
    assert any("提携・承認・後援関係はありません" in item.value for item in app.caption)


def test_xml_unsupported_text_disables_zwo_but_json_round_trip_still_works():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    workout = replace(make_preset("sst"), description="JSON allows control: \x01")
    app.text_area(key="json_text").set_value(to_json(workout)).run()
    app.button(key="load_text").click().run()
    assert not app.exception
    assert any("ZWOを出力できません" in item.value for item in app.error)
    buttons = downloads(app)
    assert buttons["download_zwo"].disabled
    assert not buttons["download_json"].disabled
    assert from_json(to_json(app.session_state["workout"])) == workout


def test_invalid_header_disables_both_downloads_and_preserves_applied_workout():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    original = app.session_state["workout"]
    app.text_input(key="name_0").set_value(" ").run()
    assert not app.exception
    assert app.session_state["workout"] == original
    assert downloads(app)["download_json"].disabled
    assert downloads(app)["download_zwo"].disabled
