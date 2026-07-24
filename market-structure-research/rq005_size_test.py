"""RQ-005の検証: RQ-001の449件の適格イベントについて、イベント前の
時価総額(サイズ)とratio(前倒し度)の間にSpearman順位相関があるか。

事前登録: research_questions/theme1_price_reaction_speed/RQ-005_size.md
RQ-001のパイプライン(compute_ar, run_reaction_speed_pipeline)は
一切変更せず、その出力(qualifying: ratio付きの449件)に時価総額を
結合するだけの追加ロジック。RQ-003・RQ-004と同じ設計を流用。
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from earnings_reaction_speed_test import (
    ALPHA_DIR,
    compute_ar,
    load_disclosure_dates,
    load_universe_prices,
    run_reaction_speed_pipeline,
)

FINS_DATA = os.path.join(ALPHA_DIR, "data")
N_PERM = 1000
SEED = 42


def load_shares_outstanding():
    """各銘柄のDiscDate順のShOutFY系列を返す({code: DataFrame[DiscDate, ShOutFY]})。"""
    result = {}
    for fn in os.listdir(FINS_DATA):
        if not fn.startswith("fins_summary_") or not fn.endswith(".csv"):
            continue
        code = fn[len("fins_summary_"):-len(".csv")]
        path = os.path.join(FINS_DATA, fn)
        if os.path.getsize(path) == 0:
            continue
        try:
            df = pd.read_csv(path, usecols=["DiscDate", "ShOutFY"], parse_dates=["DiscDate"])
        except (pd.errors.EmptyDataError, ValueError):
            continue
        df = df.dropna(subset=["ShOutFY"]).sort_values("DiscDate")
        if len(df):
            result[code] = df
    return result


def main():
    close = load_universe_prices()
    events = load_disclosure_dates()
    ar = compute_ar(close)
    trading_days = close.index
    shares = load_shares_outstanding()

    result = run_reaction_speed_pipeline(ar, trading_days, events, label="RQ-005(全適格イベント)")
    qualifying = result["qualifying"].copy()
    print(f"適格イベント総数（RQ-001と同一）: {len(qualifying)}")

    mcap_values = []
    for code, date in zip(qualifying["code"], qualifying["event_date"]):
        pos = trading_days.searchsorted(date)
        if pos <= 0 or code not in close.columns or code not in shares:
            mcap_values.append(np.nan)
            continue
        pre_price = close[code].iloc[pos - 1]
        sh_df = shares[code]
        prior = sh_df[sh_df["DiscDate"] < date]
        if prior.empty or pd.isna(pre_price):
            mcap_values.append(np.nan)
            continue
        sh_out = prior.iloc[-1]["ShOutFY"]
        mcap_values.append(pre_price * sh_out)
    qualifying["market_cap"] = mcap_values

    before = len(qualifying)
    qualifying = qualifying.dropna(subset=["market_cap"])
    print(f"時価総額が計算できたイベント: {len(qualifying)}/{before}")

    rho, _ = spearmanr(qualifying["market_cap"], qualifying["ratio"])
    print(f"Spearman相関係数（実測）: {rho:.4f}")

    rng = np.random.default_rng(SEED)
    mcap_arr = qualifying["market_cap"].to_numpy()
    ratio_arr = qualifying["ratio"].to_numpy()
    null_rhos = []
    for _ in range(N_PERM):
        shuffled = rng.permutation(mcap_arr)
        r, _ = spearmanr(shuffled, ratio_arr)
        null_rhos.append(r)
    null_rhos = np.array(null_rhos)

    p_value = (np.abs(null_rhos) >= abs(rho)).mean()
    print(f"Permutation null: mean={null_rhos.mean():.4f} std={null_rhos.std():.4f}")
    print(f"両側p値: {p_value:.4f}")
    print(f"H6判定（p<0.05で支持）: {'支持' if p_value < 0.05 else '棄却'}")

    qualifying.to_csv(os.path.join(FINS_DATA, "rq005_events_with_market_cap.csv"), index=False)


if __name__ == "__main__":
    main()
