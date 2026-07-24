"""RQ-007の検証: RQ-001の449件の適格イベントについて、決算開示の種別
(FY/四半期)によってratioに有意な差があるか。

事前登録: research_questions/theme2_arbitrage_agents/
RQ-007_disclosure_type_constraint.md
RQ-001のパイプライン(compute_ar, run_reaction_speed_pipeline)は
一切変更せず、その出力(qualifying: ratio付きの449件)にDocTypeを
結合するだけの追加ロジック。RQ-002の教訓(群間差そのものを検定する
設計にする)を踏まえ、群ラベルのシャッフルによる直接比較を行う。
"""
import os

import numpy as np
import pandas as pd

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


def load_doc_types():
    """{code: DataFrame[DiscDate, DocType]}を返す。"""
    result = {}
    for fn in os.listdir(FINS_DATA):
        if not fn.startswith("fins_summary_") or not fn.endswith(".csv"):
            continue
        code = fn[len("fins_summary_"):-len(".csv")]
        path = os.path.join(FINS_DATA, fn)
        if os.path.getsize(path) == 0:
            continue
        try:
            df = pd.read_csv(path, usecols=["DiscDate", "DocType"], parse_dates=["DiscDate"])
        except (pd.errors.EmptyDataError, ValueError):
            continue
        df = df.dropna(subset=["DocType"])
        if len(df):
            result[code] = df
    return result


def classify(doc_type):
    if "FY" in doc_type:
        return "FY"
    if any(q in doc_type for q in ("1Q", "2Q", "3Q")):
        return "Q"
    return None


def main():
    close = load_universe_prices()
    events = load_disclosure_dates()
    ar = compute_ar(close)
    trading_days = close.index
    doc_types = load_doc_types()

    result = run_reaction_speed_pipeline(ar, trading_days, events, label="RQ-007(全適格イベント)")
    qualifying = result["qualifying"].copy()
    print(f"適格イベント総数（RQ-001と同一）: {len(qualifying)}")

    groups = []
    car20_abs = []
    for code, date in zip(qualifying["code"], qualifying["event_date"]):
        if code not in doc_types:
            groups.append(None)
            continue
        dt_df = doc_types[code]
        match = dt_df[dt_df["DiscDate"] < date]
        if match.empty:
            groups.append(None)
            continue
        groups.append(classify(match.iloc[-1]["DocType"]))
    qualifying["group"] = groups

    before = len(qualifying)
    qualifying = qualifying.dropna(subset=["group"])
    print(f"分類できたイベント: {len(qualifying)}/{before}")
    print(qualifying["group"].value_counts())

    ratio = qualifying["ratio"].to_numpy()
    is_fy = (qualifying["group"] == "FY").to_numpy()

    observed_diff = ratio[is_fy].mean() - ratio[~is_fy].mean()
    print(f"観測された差 (FY平均 - Q平均): {observed_diff:.4f}")
    print(f"FY平均: {ratio[is_fy].mean():.4f} (n={is_fy.sum()}), "
          f"Q平均: {ratio[~is_fy].mean():.4f} (n={(~is_fy).sum()})")

    rng = np.random.default_rng(SEED)
    n = len(ratio)
    n_fy = is_fy.sum()
    null_diffs = []
    for _ in range(N_PERM):
        perm_is_fy = np.zeros(n, dtype=bool)
        perm_is_fy[rng.choice(n, size=n_fy, replace=False)] = True
        null_diffs.append(ratio[perm_is_fy].mean() - ratio[~perm_is_fy].mean())
    null_diffs = np.array(null_diffs)

    p_value = (np.abs(null_diffs) >= abs(observed_diff)).mean()
    print(f"Permutation null: mean={null_diffs.mean():.4f} std={null_diffs.std():.4f}")
    print(f"両側p値: {p_value:.4f}")
    print(f"H7判定（p<0.05で支持）: {'支持' if p_value < 0.05 else '棄却'}")

    # Alternative Explanationの反証コスト最小項目を同時に確認: |CAR_20|(サプライズの代理)がFY/Qで違うか
    car20_abs = qualifying["abs_car20"].to_numpy()
    car20_diff = car20_abs[is_fy].mean() - car20_abs[~is_fy].mean()
    print(f"\n[参考] |CAR_20|平均の差 (FY-Q): {car20_diff:.4f} "
          f"(FY={car20_abs[is_fy].mean():.4f}, Q={car20_abs[~is_fy].mean():.4f})")


if __name__ == "__main__":
    main()
