"""RQ-004の検証: RQ-001の449件の適格イベントについて、イベント前の
実現ボラティリティとratio(前倒し度)の間にSpearman順位相関があるか。

事前登録: research_questions/theme1_price_reaction_speed/
RQ-004_volatility_and_observable_validity.md
RQ-001のパイプライン(compute_ar, run_reaction_speed_pipeline)は
一切変更せず、その出力(qualifying: ratio付きの449件)にボラティリティ
を結合するだけの追加ロジック。RQ-003と同じ設計を流用。
"""
import os

import numpy as np
from scipy.stats import spearmanr

from earnings_reaction_speed_test import (
    compute_ar,
    load_disclosure_dates,
    load_universe_prices,
    run_reaction_speed_pipeline,
)

VOL_WINDOW = 60
N_PERM = 1000
SEED = 42


def main():
    close = load_universe_prices()
    events = load_disclosure_dates()
    ar = compute_ar(close)
    logret = np.log(close / close.shift(1))
    trading_days = close.index

    result = run_reaction_speed_pipeline(ar, trading_days, events, label="RQ-004(全適格イベント)")
    qualifying = result["qualifying"].copy()
    print(f"適格イベント総数（RQ-001と同一）: {len(qualifying)}")

    vol_values = []
    for code, date in zip(qualifying["code"], qualifying["event_date"]):
        pos = trading_days.searchsorted(date)
        if pos - VOL_WINDOW < 0 or code not in logret.columns:
            vol_values.append(np.nan)
            continue
        window = logret[code].iloc[pos - VOL_WINDOW: pos]
        vol_values.append(window.std())
    qualifying["volatility"] = vol_values

    before = len(qualifying)
    qualifying = qualifying.dropna(subset=["volatility"])
    print(f"ボラティリティが計算できたイベント: {len(qualifying)}/{before}")

    rho, _ = spearmanr(qualifying["volatility"], qualifying["ratio"])
    print(f"Spearman相関係数（実測）: {rho:.4f}")

    rng = np.random.default_rng(SEED)
    vol_arr = qualifying["volatility"].to_numpy()
    ratio_arr = qualifying["ratio"].to_numpy()
    null_rhos = []
    for _ in range(N_PERM):
        shuffled = rng.permutation(vol_arr)
        r, _ = spearmanr(shuffled, ratio_arr)
        null_rhos.append(r)
    null_rhos = np.array(null_rhos)

    p_value = (np.abs(null_rhos) >= abs(rho)).mean()
    print(f"Permutation null: mean={null_rhos.mean():.4f} std={null_rhos.std():.4f}")
    print(f"両側p値: {p_value:.4f}")
    print(f"H5判定（p<0.05で支持）: {'支持' if p_value < 0.05 else '棄却'}")

    qualifying.to_csv(os.path.join(os.path.dirname(__file__), "data", "rq004_events_with_volatility.csv"), index=False)


if __name__ == "__main__":
    main()
