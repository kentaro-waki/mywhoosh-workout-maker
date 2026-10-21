"""Streamlit entry point. Run with the project virtual environment."""

from dataclasses import replace

import streamlit as st

from workout_maker.calculations import format_duration, summarize, timeline
from workout_maker.chart import build_figure
from workout_maker.editing import (
    delete_interval,
    duplicate_interval,
    insert_after,
    move_interval,
    update_interval,
)
from workout_maker.exporters.zwo import to_zwo
from workout_maker.models import (
    KIND_LABELS,
    KINDS,
    MAX_DURATION_SECONDS,
    MAX_INTERVALS,
    Interval,
)
from workout_maker.presets import PRESET_LABELS, PRESET_NOTE, make_preset
from workout_maker.storage import from_json, to_json

st.set_page_config(page_title="Workout Maker", page_icon="🚲", layout="wide")

if "workout" not in st.session_state:
    st.session_state.workout = make_preset("4x8")
    st.session_state.revision = 0
    st.session_state.selected_index = 0


def store_workout(workout, selected=0):
    st.session_state.workout = workout
    st.session_state.selected_index = min(max(selected, 0), len(workout.intervals) - 1)
    st.session_state.revision += 1
    st.session_state.pop("header_error", None)


def change_header():
    revision = st.session_state.revision
    try:
        st.session_state.workout = replace(
            st.session_state.workout,
            ftp_watts=st.session_state[f"ftp_{revision}"],
            name=st.session_state[f"name_{revision}"],
            description=st.session_state[f"description_{revision}"],
        )
        st.session_state.pop("header_error", None)
    except ValueError as exc:
        st.session_state.header_error = f"入力を確認してください：{exc}"


def import_payload(payload):
    try:
        candidate = from_json(payload)
    except ValueError as exc:
        st.error(f"読み込めません。現在のワークアウトは保持しています：{exc}")
        return
    store_workout(candidate)
    st.session_state.notice = "JSONを読み込みました。"
    st.rerun()


st.title("Workout Maker")
st.caption(
    "FTPから目標出力を計算し、区間を編集・保存する非公式の個人開発ツール。"
    "MyWhooshの運営元との提携・承認・後援関係はありません。"
)
st.info(PRESET_NOTE)
if notice := st.session_state.pop("notice", None):
    st.success(notice)

with st.expander("プリセット・JSONを読み込む", expanded=False):
    st.selectbox(
        "プリセット", list(PRESET_LABELS), format_func=PRESET_LABELS.get, key="preset_choice"
    )
    st.caption("読み込むと現在の編集内容を置き換えます。必要なら先にJSONを保存してください。")
    if st.button("プリセットを読み込む", key="load_preset"):
        store_workout(
            make_preset(st.session_state.preset_choice, st.session_state.workout.ftp_watts)
        )
        st.rerun()
    uploaded = st.file_uploader("このアプリで保存したJSON", type=["json"], key="json_upload")
    if st.button("ファイルから読み込む", disabled=uploaded is None, key="load_file"):
        import_payload(uploaded.getvalue())
    st.text_area("JSONテキストから読み込む", key="json_text", height=100)
    if st.button("テキストから読み込む", key="load_text"):
        import_payload(st.session_state.json_text)

workout = st.session_state.workout
revision = st.session_state.revision
st.text_input(
    "ワークアウト名",
    value=workout.name,
    max_chars=200,
    key=f"name_{revision}",
    on_change=change_header,
)
st.number_input(
    "FTP（W）",
    min_value=0.1,
    value=float(workout.ftp_watts),
    step=1.0,
    key=f"ftp_{revision}",
    on_change=change_header,
)
st.text_area(
    "説明",
    value=workout.description,
    max_chars=10000,
    key=f"description_{revision}",
    on_change=change_header,
    height=80,
)
if "header_error" in st.session_state:
    st.error(st.session_state.header_error)

# Header callbacks run before this rerun; summaries always use the validated model.
workout = st.session_state.workout
summary = summarize(workout)
columns = st.columns(3)
columns[0].metric("合計時間（分:秒）", format_duration(summary.duration_seconds))
columns[1].metric("平均目標出力", f"{summary.average_watts:.1f} W")
columns[2].metric("予定仕事量", f"{summary.work_kj:.1f} kJ")
st.plotly_chart(build_figure(workout), width="stretch", config={"displaylogo": False})
st.caption(
    "区間の幅は継続時間に比例します。色は区分を表し、強度から自動判定しません。"
    "予定仕事量は目標値からの計算で、実際の走行記録ではありません。"
)

st.subheader("区間を編集")
selected = st.selectbox(
    "編集する区間",
    list(range(len(workout.intervals))),
    index=st.session_state.selected_index,
    format_func=lambda i: (
        f"{i + 1}. {workout.intervals[i].name} "
        f"({format_duration(workout.intervals[i].duration_seconds)})"
    ),
    key=f"selected_{revision}",
)
st.session_state.selected_index = selected
item = workout.intervals[selected]
with st.form(f"edit_{revision}_{selected}"):
    name = st.text_input("区間名", value=item.name, max_chars=200)
    minutes = st.number_input(
        "時間（分）",
        min_value=0,
        value=item.duration_seconds // 60,
        max_value=MAX_DURATION_SECONDS // 60,
        step=1,
    )
    seconds = st.number_input(
        "時間（秒）", min_value=0, max_value=59, value=item.duration_seconds % 60, step=1
    )
    percent = st.number_input(
        "目標（%FTP）", min_value=0.0, value=float(item.target_percent), step=1.0
    )
    kind = st.selectbox("区分", KINDS, index=KINDS.index(item.kind), format_func=KIND_LABELS.get)
    submitted = st.form_submit_button("区間の変更を適用")
if submitted:
    try:
        changed = Interval(name, minutes * 60 + seconds, percent, kind)
        candidate = update_interval(workout, selected, changed)
    except ValueError as exc:
        st.error(f"変更できません。適用前の内容を保持しています：{exc}")
    else:
        store_workout(candidate, selected)
        st.rerun()
st.caption("区間フォームの内容は「変更を適用」でグラフと保存データに反映します。")

buttons = st.columns(3)
if buttons[0].button(
    "後ろに区間を追加", key="add_interval", disabled=len(workout.intervals) >= MAX_INTERVALS
):
    store_workout(insert_after(workout, selected, Interval("新しい区間", 60, 50)), selected + 1)
    st.rerun()
if buttons[1].button(
    "区間を複製", key="duplicate_interval", disabled=len(workout.intervals) >= MAX_INTERVALS
):
    store_workout(duplicate_interval(workout, selected), selected + 1)
    st.rerun()
if buttons[2].button("区間を削除", disabled=len(workout.intervals) == 1, key="delete_interval"):
    store_workout(delete_interval(workout, selected), selected)
    st.rerun()
ordering = st.columns(2)
if ordering[0].button("1つ前へ", disabled=selected == 0, key="move_up"):
    store_workout(move_interval(workout, selected, -1), selected - 1)
    st.rerun()
if ordering[1].button("1つ後へ", disabled=selected == len(workout.intervals) - 1, key="move_down"):
    store_workout(move_interval(workout, selected, 1), selected + 1)
    st.rerun()

with st.expander("すべての区間を確認"):
    st.dataframe(
        [
            {
                "順番": row.index + 1,
                "区間": row.name,
                "区分": KIND_LABELS[row.kind],
                "開始": format_duration(row.start_seconds),
                "長さ": format_duration(row.duration_seconds),
                "%FTP": row.target_percent,
                "目標W": round(row.power_watts, 1),
            }
            for row in timeline(workout)
        ],
        hide_index=True,
        width="stretch",
    )

st.subheader("保存")
try:
    saved_json = to_json(workout).encode("utf-8")
except ValueError as exc:
    saved_json = b""
    st.error(f"保存できません。区間名や説明を短くしてください：{exc}")
st.download_button(
    "JSONを保存",
    saved_json,
    file_name="workout.json",
    mime="application/json",
    key="download_json",
    disabled="header_error" in st.session_state or not saved_json,
    on_click="ignore",
)
st.caption(
    "JSONをダウンロードして保管してください。ブラウザ再読込や接続終了で"
    "編集中の内容が失われる場合があります。"
)
st.warning("JSONは本アプリ専用の編集・保存形式です。MyWhooshに直接取り込む形式ではありません。")

st.subheader("ZWO出力（試験機能）")
st.warning(
    "試験機能です。4種類のサンプルについて、公式MyWhoosh Workout Builderでの"
    "区間数・合計時間の一致をユーザーが確認しました（報告記録日: 2026-10-21）。"
    "個々の区間の出力・順序、アプリへの同期、実走時の出力制御、他環境は未検証です。"
    "目標Wは取り込み先のFTPに依存します。取り込み後に時間と出力を確認してください。"
)
st.caption(
    "全区間を一定出力のSteadyStateとして、順番と秒数・FTP比率を保持して出力します。"
    "反復圧縮やランプへの変換は行いません。個別の区間名・区分・色はZWOへ保存しません。"
    "再編集のため、元のJSONも保存してください。"
)
try:
    saved_zwo = to_zwo(workout)
except ValueError as exc:
    saved_zwo = b""
    st.error(f"ZWOを出力できません。値や文字を変更せず中止しました：{exc}")
st.download_button(
    "ZWOをダウンロード（試験）",
    saved_zwo,
    file_name="workout.zwo",
    mime="application/xml",
    key="download_zwo",
    disabled="header_error" in st.session_state or not saved_zwo,
    on_click="ignore",
)
