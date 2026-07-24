"""RQ-003の検証: RQ-001の449件の適格イベントについて、イベント前の
流動性(連続変数)とratio(前倒し度)の間にSpearman順位相関があるか。

事前登録: research_questions/theme1_price_reaction_speed/
RQ-003_liquidity_continuous.md
RQ-001のパイプライン(compute_ar, run_reaction_speed_pipeline)は
一切変更せず、その出力(qualifying: ratio付きの449件)に流動性を
結合するだけの追加ロジック。
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from earnings_reaction_speed_test import (
    compute_ar,
    load_disclosure_dates,
    load_universe_prices,
    run_reaction_speed_pipeline,
)
from rq002_liquidity_blocking_test import load_universe_volume

LIQ_WINDOW = 60
N_PERM = 1000
SEED = 42


def main():
    close = load_universe_prices()
    volume = load_universe_volume()
    events = load_disclosure_dates()
    ar = compute_ar(close)
    dollar_vol = close * volume
    trading_days = close.index

    result = run_reaction_speed_pipeline(ar, trading_days, events, label="RQ-003(全適格イベント)")
    qualifying = result["qualifying"].copy()
    print(f"適格イベント総数（RQ-001と同一）: {len(qualifying)}")

    liq_values = []
    for code, date in zip(qualifying["code"], qualifying["event_date"]):
        pos = trading_days.searchsorted(date)
        if pos - LIQ_WINDOW < 0 or code not in dollar_vol.columns:
            liq_values.append(np.nan)
            continue
        liq_values.append(dollar_vol[code].iloc[pos - LIQ_WINDOW: pos].mean())
    qualifying["liquidity"] = liq_values

    before = len(qualifying)
    qualifying = qualifying.dropna(subset=["liquidity"])
    print(f"流動性が計算できたイベント: {len(qualifying)}/{before}")

    rho, _ = spearmanr(qualifying["liquidity"], qualifying["ratio"])
    print(f"Spearman相関係数（実測）: {rho:.4f}")

    rng = np.random.default_rng(SEED)
    liq_arr = qualifying["liquidity"].to_numpy()
    ratio_arr = qualifying["ratio"].to_numpy()
    null_rhos = []
    for _ in range(N_PERM):
        shuffled = rng.permutation(liq_arr)
        r, _ = spearmanr(shuffled, ratio_arr)
        null_rhos.append(r)
    null_rhos = np.array(null_rhos)

    p_value = (np.abs(null_rhos) >= abs(rho)).mean()
    print(f"Permutation null: mean={null_rhos.mean():.4f} std={null_rhos.std():.4f}")
    print(f"両側p値: {p_value:.4f}")
    print(f"H3判定（p<0.05で支持）: {'支持' if p_value < 0.05 else '棄却'}")

    qualifying.to_csv(os.path.join(os.path.dirname(__file__), "data", "rq003_events_with_liquidity.csv"), index=False)


if __name__ == "__main__":
    main()
