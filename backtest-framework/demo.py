"""全段階を実データでつなぐデモ。

「多数のパラメータで戦略を試し、最良を選ぶ」典型的な研究プロセスを再現し、
その最良戦略が **本物のエッジか、過学習の産物か** を統計検定で判定する。

流れ:
  Stage1 データ監査 → Stage6 統計評価(DSR/PBO/RealityCheck) → Stage5 ロバスト性
"""
import numpy as np
import pandas as pd
import requests

import data_audit
import engines
import robustness
import stats_eval

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch(symbol: str, range_: str = "5y") -> pd.DataFrame:
    r = requests.get(f"{CHART}/{symbol}",
                     params={"range": range_, "interval": "1d",
                             "includeAdjustedClose": "true"},
                     headers=_HEADERS, timeout=25).json()
    res = r["chart"]["result"][0]
    ind = res["indicators"]
    close = ind["adjclose"][0]["adjclose"] if ind.get("adjclose") else ind["quote"][0]["close"]
    df = pd.DataFrame(
        {"date": pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_localize(None),
         "close": close, "volume": ind["quote"][0]["volume"]}
    ).dropna(subset=["close"]).set_index("date").sort_index()
    return df


def main(symbol="^N225"):
    print(f"対象: {symbol}\n")
    df = fetch(symbol)

    # --- Stage 1: データ監査 ---
    print(data_audit.format_report(data_audit.audit(df)))

    # --- 多数のSMAパラメータで戦略を生成（＝データスヌーピングの現場） ---
    close = df["close"]
    fasts = [5, 10, 15, 20, 25, 30, 40, 50]
    slows = [50, 60, 75, 100, 120, 150, 180, 200]
    combos = [(f, s) for f in fasts for s in slows if f < s]

    ret_cols = {}
    for f, s in combos:
        pos = engines.signals_sma(close, f, s)
        eq = engines.vectorized(close, pos)
        ret_cols[f"sma_{f}_{s}"] = eq.pct_change().fillna(0.0)
    R = pd.DataFrame(ret_cols)
    print(f"\n試した戦略数: {R.shape[1]}（SMAクロスのパラメータ総当たり）")

    sharpes = {c: stats_eval.sharpe(R[c].values) for c in R.columns}
    best = max(sharpes, key=sharpes.get)
    print(f"見かけ上の最良: {best}  Sharpe(年率)={sharpes[best]:+.2f}")

    # --- Stage 6: 統計評価（その最良は本物か？） ---
    print("\n" + "=" * 56)
    print("Stage 6: 統計評価 ―― 最良戦略は本物か、過学習か")
    print("=" * 56)
    sr_trials = [stats_eval.sharpe(R[c].values) / np.sqrt(252) for c in R.columns]
    dsr = stats_eval.deflated_sharpe_ratio(R[best].values, sr_trials)
    pbo = stats_eval.pbo_cscv(R.values, n_splits=8)
    rc = stats_eval.whites_reality_check(R.values, n_boot=800)
    print(f"  Deflated Sharpe Ratio : {dsr['dsr']:.3f}  "
          f"(観測SR/期待最大SR = {dsr['sr_observed_per_period']:.3f}/"
          f"{dsr['sr_expected_max_per_period']:.3f}) ※高いほど本物")
    print(f"  PBO (過学習確率)      : {pbo['pbo']:.3f}  "
          f"({pbo['n_combinations']}通りのCSCV) ※低いほど良い")
    print(f"  White's Reality Check : p={rc['p_value']:.3f}  ※低いほど優位は本物")

    verdict = (
        "○ 統計的に本物のエッジの可能性" if (dsr["dsr"] > 0.9 and pbo["pbo"] < 0.5 and rc["p_value"] < 0.05)
        else "× 過学習/データスヌーピングの産物の疑いが濃い"
    )
    print(f"\n  総合判定: {verdict}")

    # --- Stage 5: 最良戦略のロバスト性 ---
    print("\n" + "=" * 56)
    print("Stage 5: 最良戦略のロバスト性（モンテカルロ・ブートストラップ）")
    print("=" * 56)
    mc = robustness.monte_carlo_shuffle(R[best].values, n_sims=1500)
    bs = robustness.stationary_bootstrap(R[best].values, n_boot=1500)
    print(f"  観測 最大DD {mc['observed_max_dd']*100:.1f}% / "
          f"シャッフル分布 中央値{mc['maxdd_p50']*100:.1f}% "
          f"最悪{mc['maxdd_worst']*100:.1f}%（順序次第でここまで悪化しうる）")
    print(f"  Sharpe 95%CI [{bs['sharpe_ci95_low']:+.2f}, {bs['sharpe_ci95_high']:+.2f}]  "
          f"Sharpe>0の確率 {bs['prob_sharpe_positive']*100:.0f}%")

    print(
        "\n注意: これは教育用デモ。SMAクロスの総当たりで『最良』を選ぶ行為自体が"
        "\nデータスヌーピングであり、DSR/PBO/RealityCheckはまさにそれを暴くための道具。"
    )


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "^N225")
