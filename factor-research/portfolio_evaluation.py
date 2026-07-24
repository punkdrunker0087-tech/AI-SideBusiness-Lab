"""8. ポートフォリオ評価 ―― 複数ファクターを組み合わせた際の分散効果・相関・
リスク配分・回転率を評価する。
"""
import numpy as np
import pandas as pd


def rebalance_dates(index: pd.DatetimeIndex, freq: str) -> list:
    """実際の最終取引日を返す（暦日ラベルの非取引日問題を回避）。"""
    s = pd.Series(index, index=index)
    return s.resample(freq).last().dropna().tolist()


def factor_return_series(feature: pd.DataFrame, close: pd.DataFrame,
                         rebalance: str = "ME", q: int = 5) -> pd.Series:
    """特徴量の上位分位−下位分位（ロング・ショート）の日次リターン系列。"""
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
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    return (held * ret).sum(axis=1), turnover


def correlation_matrix(factor_returns: dict) -> pd.DataFrame:
    return pd.DataFrame(factor_returns).corr()


def diversification_ratio(weights: np.ndarray, factor_returns: dict) -> float:
    """ファクター合成時の分散化比率 = 加重平均ボラ / 合成ポートのボラ。"""
    df = pd.DataFrame(factor_returns).dropna()
    vols = df.std().values
    weighted_avg_vol = weights @ vols
    combined = (df.values * weights).sum(axis=1)
    combined_vol = combined.std()
    return float(weighted_avg_vol / combined_vol) if combined_vol else np.nan


def equal_risk_weights(factor_returns: dict) -> np.ndarray:
    """簡易リスクパリティ: 各ファクターのボラの逆数で重み付け。"""
    df = pd.DataFrame(factor_returns).dropna()
    inv_vol = 1.0 / df.std()
    return (inv_vol / inv_vol.sum()).values


def turnover_summary(turnovers: dict) -> pd.DataFrame:
    rows = [{"ファクター": name, "年率回転率": float(t.mean() * 252)} for name, t in turnovers.items()]
    return pd.DataFrame(rows)
