"""H2の検証: 決算開示後、異常リターンの何%が最初の3営業日に実現するか。

事前登録: hypotheses/H2_earnings_reaction_speed.md
設計を先に固定してから実行すること。ここでの数値を見てから設計
（イベント窓・閾値・モデル）を変更してはならない。
"""
import os

import numpy as np
import pandas as pd

ALPHA_DIR = os.path.dirname(__file__)
AQM_DATA = os.path.join(ALPHA_DIR, "..", "aqm-strategy", "data")
FINS_DATA = os.path.join(ALPHA_DIR, "data")

CAR_SHORT = 3
CAR_LONG = 20
MIN_ABS_CAR20 = 0.01
N_PERM = 1000
SEED = 42


def load_universe_prices():
    closes = {}
    for fn in os.listdir(AQM_DATA):
        if fn.endswith("_15y.csv"):
            code = fn.replace("_15y.csv", "").replace(".T", "")
            df = pd.read_csv(os.path.join(AQM_DATA, fn), parse_dates=["date"], index_col="date")
            closes[code] = df["close"]
    close = pd.DataFrame(closes).sort_index()
    return close


def load_disclosure_dates():
    events = {}
    for fn in os.listdir(FINS_DATA):
        if not fn.startswith("fins_summary_") or not fn.endswith(".csv"):
            continue
        code = fn[len("fins_summary_"):-len(".csv")]
        path = os.path.join(FINS_DATA, fn)
        if os.path.getsize(path) == 0:
            continue
        try:
            df = pd.read_csv(path, usecols=["DiscDate"], parse_dates=["DiscDate"])
        except (pd.errors.EmptyDataError, ValueError):
            continue
        dates = df["DiscDate"].dropna().unique()
        if len(dates):
            events[code] = sorted(pd.to_datetime(dates))
    return events


def main():
    close = load_universe_prices()
    events = load_disclosure_dates()

    logret = np.log(close / close.shift(1))
    market = logret.mean(axis=1)  # 日経225近似ユニバースの単純平均＝市場リターンの代理
    ar = logret.sub(market, axis=0)  # 市場調整後異常収益

    trading_days = close.index

    rows = []
    for code, disc_dates in events.items():
        if code not in ar.columns:
            continue
        series = ar[code]
        for d in disc_dates:
            pos = trading_days.searchsorted(d, side="right")  # DiscDate翌営業日
            if pos <= 0 or pos + CAR_LONG >= len(trading_days):
                continue
            window = series.iloc[pos: pos + CAR_LONG + 1]
            if window.isna().any():
                continue
            car3 = window.iloc[:CAR_SHORT + 1].sum()
            car20 = window.sum()
            rows.append({"code": code, "event_date": trading_days[pos],
                         "car3": car3, "car20": car20, "window": window.values})

    events_df = pd.DataFrame([{k: v for k, v in r.items() if k != "window"} for r in rows])
    print(f"検出したイベント総数: {len(events_df)}")

    events_df["abs_car20"] = events_df["car20"].abs()
    qualifying = events_df[events_df["abs_car20"] >= MIN_ABS_CAR20].copy()
    print(f"|CAR_20|>=1%のフィルタ後: {len(qualifying)}件")

    qualifying["ratio"] = qualifying["car3"].abs() / qualifying["car20"].abs()
    median_ratio = qualifying["ratio"].median()
    mean_ratio = qualifying["ratio"].mean()
    print(f"ratio中央値: {median_ratio:.4f}")
    print(f"ratio平均値: {mean_ratio:.4f}")
    print(f"H2判定（中央値>=0.80で支持）: {'支持' if median_ratio >= 0.80 else '棄却'}")

    windows = {r["code"] + str(r["event_date"]): r["window"] for r in rows}
    qual_keys = [c + str(d) for c, d in zip(qualifying["code"], qualifying["event_date"])]
    qual_windows = [windows[k] for k in qual_keys]

    rng = np.random.default_rng(SEED)
    perm_means = []
    for _ in range(N_PERM):
        ratios = []
        for w in qual_windows:
            shuffled = rng.permutation(w)
            c3 = shuffled[:CAR_SHORT + 1].sum()
            c20 = shuffled.sum()
            if abs(c20) < 1e-9:
                continue
            ratios.append(abs(c3) / abs(c20))
        perm_means.append(np.mean(ratios))
    perm_means = np.array(perm_means)

    p_value = (perm_means >= mean_ratio).mean()
    print(f"Permutation null平均: {perm_means.mean():.4f} (std {perm_means.std():.4f})")
    print(f"実際の平均ratio: {mean_ratio:.4f}")
    print(f"片側p値（実際 >= null分布上での比率）: {p_value:.4f}")

    events_df.to_csv(os.path.join(ALPHA_DIR, "data", "h2_events_raw.csv"), index=False)
    qualifying.to_csv(os.path.join(ALPHA_DIR, "data", "h2_qualifying_events.csv"), index=False)


if __name__ == "__main__":
    main()
