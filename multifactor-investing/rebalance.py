"""リバランス ―― 取引コスト・回転率・流動性を考慮してポートフォリオを調整する。

同じファクター戦略でも、リバランス頻度を上げるほど特性追随は速いが
回転率とコストが増え、正味リターンを削る。頻度別に比較する。
"""
import numpy as np
import pandas as pd

from correlation import rebalance_dates


def rebalance_backtest(feature: pd.DataFrame, close: pd.DataFrame,
                       rebalance: str, cost_bps: float = 15.0, q: int = 5) -> dict:
    """指定リバランス頻度でロング・ショート戦略を回し、回転率・コスト後成績を返す。"""
    ret = close.pct_change().fillna(0.0)
    rebal_days = rebalance_dates(close.index, rebalance)

    weights = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for t in rebal_days:
        s = feature.loc[t].dropna() if t in feature.index else pd.Series(dtype=float)
        if len(s) < q * 2:
            continue
        k = max(1, len(s) // q)
        longs, shorts = s.nlargest(k).index, s.nsmallest(k).index
        w = pd.Series(0.0, index=close.columns)
        w[longs] = 1.0 / k
        w[shorts] = -1.0 / k
        weights.loc[t] = w
    weights = weights.ffill().fillna(0.0)

    held = weights.shift(1).fillna(0.0)
    gross_ret = (held * ret).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    cost = turnover * (cost_bps / 1e4)
    net_ret = gross_ret - cost

    n_years = len(close) / 252
    ann_turnover = turnover.sum() / max(n_years, 1e-9)
    gross_total = float((1 + gross_ret).prod() - 1)
    net_total = float((1 + net_ret).prod() - 1)
    return {
        "rebalance": rebalance,
        "n_rebalances": len(rebal_days),
        "annual_turnover": float(ann_turnover),
        "gross_total_return": gross_total,
        "net_total_return": net_total,
        "cost_drag": gross_total - net_total,
    }


def compare_frequencies(feature: pd.DataFrame, close: pd.DataFrame,
                        frequencies=("W", "ME", "QE"), cost_bps: float = 15.0) -> pd.DataFrame:
    """複数のリバランス頻度を比較する（回転率とコストのトレードオフ）。"""
    rows = [rebalance_backtest(feature, close, f, cost_bps) for f in frequencies]
    return pd.DataFrame(rows)
