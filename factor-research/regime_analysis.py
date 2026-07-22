"""6. 市場環境ごとの分析 ―― 景気局面・市場ストレス時でファクター特性がどう変わるか。"""
import numpy as np
import pandas as pd

import risk_metrics


def classify_regime(bench_close: pd.Series, trend_window: int = 60, vol_window: int = 20) -> pd.DataFrame:
    """ベンチマークからトレンド局面・ボラ局面を判定する（先読みなし）。"""
    ma = bench_close.rolling(trend_window).mean()
    trend = np.where(bench_close > ma, "強気", "弱気")

    logret = np.log(bench_close / bench_close.shift(1))
    rv = logret.rolling(vol_window).std()
    rv_med = rv.expanding(min_periods=vol_window).median()
    vol = np.where(rv > rv_med, "高ボラ", "低ボラ")

    return pd.DataFrame({"trend": trend, "vol": vol}, index=bench_close.index)


def performance_by_regime(factor_returns: pd.Series, regimes: pd.DataFrame,
                          dimension: str = "trend") -> pd.DataFrame:
    """ファクターの日次リターンをレジーム別に集計し、リスク指標を比較する。"""
    reg = regimes[dimension].reindex(factor_returns.index)
    rows = []
    for label in pd.unique(reg.dropna()):
        sub = factor_returns[reg == label]
        if len(sub) < 20:
            continue
        m = risk_metrics.full_report(sub)
        m["regime"] = label
        m["n_days"] = len(sub)
        rows.append(m)
    return pd.DataFrame(rows).set_index("regime") if rows else pd.DataFrame()
