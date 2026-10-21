"""Synthetic editable examples; no claim of scientific optimality."""

from workout_maker.models import Interval, Workout

PRESET_LABELS = {"4x8": "4×8分", "30_15": "30/15（3セット×10回）", "sst": "SST（2×15分）"}
PRESET_NOTE = "編集用の例です。科学的な最適性や個人への適合性を保証するものではありません。"


def make_preset(key: str, ftp_watts: float = 250) -> Workout:
    rows = [Interval("ウォームアップ", 600, 50, "warmup")]
    if key == "4x8":
        for rep in range(4):
            rows.append(Interval(f"8分 #{rep + 1}", 480, 105, "work"))
            if rep < 3:
                rows.append(Interval("回復", 180, 50, "recovery"))
    elif key == "30_15":
        for group in range(3):
            for rep in range(10):
                rows.append(Interval(f"30秒 {group + 1}-{rep + 1}", 30, 120, "work"))
                rows.append(Interval("15秒回復", 15, 50, "recovery"))
            if group < 2:
                rows.append(Interval("セット間回復", 180, 50, "recovery"))
    elif key == "sst":
        for rep in range(2):
            rows.append(Interval(f"SST #{rep + 1}", 900, 90, "work"))
            if rep == 0:
                rows.append(Interval("回復", 300, 50, "recovery"))
    else:
        raise ValueError("unknown preset")
    rows.append(Interval("クールダウン", 300, 40, "cooldown"))
    return Workout(PRESET_LABELS[key], ftp_watts, tuple(rows), PRESET_NOTE)
