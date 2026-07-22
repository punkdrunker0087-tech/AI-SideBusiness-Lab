"""AQM-01のファクター定義・パラメータ感度をDSR/PBOで検証する。

BACKLOG「既存戦略への適用: DSR/PBO/Reality CheckをAQM-01の戦略に当てる」
に対応。ユニバース拡大（25→225銘柄）でも絶対リターンが正にならなかった
ことを受け、「パラメータの選び方次第でどこかに勝ち筋がないか」を、
複数パラメータの単純なグリッドサーチ + DSR/PBOで検証する。

⚠️ これは「勝てるパラメータを探す」作業そのものが多重検定
（データスヌーピング）になりうる。そのためグリッド内の最良の結果を
そのまま採用せず、**試行回数を織り込んだDeflated Sharpe Ratio**と
**Probability of Backtest Overfitting (PBO)**で、見かけの最良が
本物か偶然かを判定する。
"""
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent / "backtest-framework"))
import stats_eval  # noqa: E402

import factors
import panel
import strategy

MOMENTUM_LOOKBACKS = [60, 120, 252]
TOP_QS = [0.1, 0.2, 0.3]
REBALANCES = ["ME", "W"]


def composite_score_custom(close, volume, momentum_lookback):
    zM = factors.zscore_cross(factors.momentum(close, lookback=momentum_lookback))
    zS = factors.zscore_cross(factors.volatility(close))
    zL = factors.zscore_cross(factors.liquidity(close, volume))
    w = strategy.WEIGHTS
    return w["M"] * zM + w["sigma"] * zS + w["L"] * zL


def main():
    print("パネル構築中（キャッシュ利用）…")
    close, volume = panel.build_panel(range_="5y", use_cache=True)
    print(f"  銘柄数: {close.shape[1]}  営業日: {close.shape[0]}\n")

    grid = list(product(MOMENTUM_LOOKBACKS, TOP_QS, REBALANCES))
    print(f"グリッド探索: momentum_lookback×top_q×rebalance = {len(grid)}通り\n")

    results = []
    ret_series = {}
    for lookback, top_q, rebalance in grid:
        score = composite_score_custom(close, volume, lookback)
        res = strategy.backtest(close, score, top_q=top_q, rebalance=rebalance)
        m = strategy.metrics(res.returns, res.equity)
        key = (lookback, top_q, rebalance)
        ret_series[key] = res.returns
        results.append({
            "momentum_lookback": lookback, "top_q": top_q, "rebalance": rebalance,
            "total_return": m["total_return"], "sharpe": m["sharpe"],
            "max_dd": m["max_drawdown"],
        })

    results_df = pd.DataFrame(results).sort_values("sharpe", ascending=False)
    print("=" * 78)
    print("全18通りのパラメータ・グリッド（Sharpe降順）")
    print("=" * 78)
    print(results_df.round(3).to_string(index=False))

    # 共通の日付インデックスへ揃えてリターン行列を構築(T×N)
    common_index = None
    for r in ret_series.values():
        common_index = r.index if common_index is None else common_index.intersection(r.index)
    returns_matrix = np.column_stack([ret_series[k].reindex(common_index).fillna(0.0).values
                                      for k in ret_series])

    per_period_sharpes = returns_matrix.mean(axis=0) / returns_matrix.std(axis=0, ddof=1)
    best_idx = int(np.nanargmax(per_period_sharpes))
    best_key = list(ret_series.keys())[best_idx]
    best_returns = returns_matrix[:, best_idx]

    dsr = stats_eval.deflated_sharpe_ratio(best_returns, per_period_sharpes)
    pbo = stats_eval.pbo_cscv(returns_matrix, n_splits=10)

    print("\n" + "=" * 78)
    print("グリッド内最良パラメータの信頼性評価（DSR・PBO）")
    print("=" * 78)
    print(f"最良パラメータ: momentum_lookback={best_key[0]}  top_q={best_key[1]}  "
         f"rebalance={best_key[2]}")
    print(f"  観測Sharpe(年率換算)={dsr['sr_observed_per_period']*np.sqrt(252):.3f}  "
         f"試行数={dsr['n_trials']}")
    print(f"  期待される最大Sharpe(偶然・年率換算)="
         f"{dsr['sr_expected_max_per_period']*np.sqrt(252):.3f}")
    print(f"  Deflated Sharpe Ratio(DSR) = {dsr['dsr']:.3f}  "
         f"(1に近いほど「本物」、0.5近辺は偶然と区別不能)")
    print(f"  PBO(過学習確率) = {pbo['pbo']:.3f}  "
         f"({pbo['n_combinations']}通りのIS/OOS分割で評価。0.5超は過学習の疑い濃厚)")

    verdict = (
        "DSRが高くPBOが低い → グリッド内最良は偶然ではなく本物の可能性がある"
        if dsr["dsr"] > 0.95 and pbo["pbo"] < 0.3
        else "DSR・PBOの基準を満たさない → グリッド内最良の好成績は"
             "多重検定による偶然（データスヌーピング）の可能性が高い"
    )
    print(f"\n判定: {verdict}")


if __name__ == "__main__":
    main()
