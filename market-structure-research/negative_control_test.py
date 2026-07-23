"""H0(ネガティブコントロール)の検証: ランダムな偽イベント日に対して、
H2と同一のパイプラインが誤って有意な前倒し反応を検出しないことを確認する。

事前登録: hypotheses/H0_negative_control.md
パイプライン本体(compute_ar, run_reaction_speed_pipeline)はH2から
一切変更せずインポートして使う。
"""
import os

import numpy as np

from earnings_reaction_speed_test import (
    ALPHA_DIR,
    compute_ar,
    load_disclosure_dates,
    load_universe_prices,
    run_reaction_speed_pipeline,
)

FAKE_SEED = 1234


def generate_fake_events(real_events, trading_days, seed=FAKE_SEED):
    rng = np.random.default_rng(seed)
    fake_events = {}
    for code, dates in real_events.items():
        n = len(dates)
        idx = rng.integers(low=0, high=len(trading_days), size=n)
        fake_events[code] = sorted(trading_days[idx])
    return fake_events


def main():
    close = load_universe_prices()
    real_events = load_disclosure_dates()
    ar = compute_ar(close)

    fake_events = generate_fake_events(real_events, close.index)
    result = run_reaction_speed_pipeline(ar, close.index, fake_events, label="H0(偽イベント)")

    verdict = "支持（有意な誤検出なし）" if result["p_value"] >= 0.05 else "棄却（誤検出のリスクあり）"
    print(f"H0判定（p>=0.05で支持）: {verdict}")
    print(f"参考: ratio平均値={result['mean_ratio']:.4f}, "
          f"Permutation null平均={result['perm_mean']:.4f}")


if __name__ == "__main__":
    main()
