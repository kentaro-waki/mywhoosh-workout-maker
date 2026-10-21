# 計算とコードの対応

## 定義と仮定

FTPを$F>0$ W、区間$i$の継続時間を$\Delta t_i>0$秒、目標割合を$q_i\geq0$ %とします。
区間内の目標出力は一定です。ランプや実際のパワー変動はこのモデルには含めません。

## 目標出力

$$
r_i=\frac{q_i}{100},\qquad P_i=Fr_i
$$

`calculations.timeline()`が`Workout.ftp_watts`と`Interval.target_percent`から計算します。
FTPが250 Wで80%なら200 Wです。FTP変更後も割合と時間を維持します。

## 時間とグラフ

$$
t_i=\sum_{j<i}\Delta t_j,\qquad
x_i=\frac{t_i+\Delta t_i/2}{60},\qquad
w_i=\frac{\Delta t_i}{60}
$$

`timeline()`が開始・終了秒を求め、`chart.build_figure()`が中心$x_i$、幅$w_i$、高さ$P_i$の棒にします。
横軸は数値の「分」です。各区間を等幅のカテゴリーにすることはありません。
隣接する棒の端点が一致し、1分区間の幅は8分区間の1/8になります。

## 合計・平均・予定仕事量

$$
T=\sum_i\Delta t_i,\qquad
\overline P=\frac{\sum_i P_i\Delta t_i}{T},\qquad
E_{\mathrm{kJ}}=\frac{\sum_i P_i\Delta t_i}{1000}
$$

`calculations.summarize()`が求めます。区間の単純平均は使いません。
1 W = 1 J/sなので、Wと秒の積はJ、1000で割るとkJです。
ここで計算するのは機械的な予定仕事量であり、実走の計測値や消費カロリーではありません。

## 手計算例

FTP=250 Wで、300秒50%、120秒100%、180秒50%とします。

$$
T=300+120+180=600\ \mathrm{s}
$$

$$
E=125\times300+250\times120+125\times180=90000\ \mathrm{J}
$$

したがって平均150 W、90 kJです。FTPを300 Wにすると全区間のWが1.2倍になり、平均180 W、108 kJです。
この例は`tests/test_calculations.py`と`examples/calculation_sample.json`で再現します。

## 学習の順序

1. `models.Interval`の1区間を読む。
2. `timeline()`の1行の出力換算と、開始時刻の累積を追う。
3. `summarize()`で単位と時間加重平均を確認する。
4. `editing.update_interval()`で不変データの変更を追う。
5. `storage.to_json()`と`from_json()`の往復を読む。
6. 最後に`app.py`の入力とモデルの接続を読む。

## 参照

- 数式は本アプリの一定目標出力モデルから直接導出しています。
- [Plotly bar charts](https://plotly.com/python/bar-charts/)
- [Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- プリセットの科学的最適性を主張する文献や実証はありません。
