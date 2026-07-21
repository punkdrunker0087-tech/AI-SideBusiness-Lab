"""6. レジーム分析 ―― 市場環境ごとに特徴量の有効性を分けて評価する。

同じ特徴量でも、トレンド局面/横ばい、高ボラ/低ボラで意味が変わる。
市場（ベンチマーク）からレジームを判定し、レジーム別のICを比較する。
"""
import numpy as np
import pandas as pd

import evaluation


def classify_regimes(market_close: pd.Series, trend_window: int = 60,
                     vol_window: int = 20) -> pd.DataFrame:
    """市場指数から各日のレジーム（トレンド方向・ボラ水準）を判定する。

    - trend: 終値がtrend_window移動平均より上=強気 / 下=弱気
    - vol  : 実現ボラが過去中央値より上=高ボラ / 下=低ボラ
    すべて時点tまでの情報で判定（先読みなし）。
    """
    ma = market_close.rolling(trend_window).mean()
    trend = np.where(market_close > ma, "強気", "弱気")

    logret = np.log(market_close / market_close.shift(1))
    rv = logret.rolling(vol_window).std()
    rv_med = rv.expanding(min_periods=vol_window).median()
    vol = np.where(rv > rv_med, "高ボラ", "低ボラ")

    return pd.DataFrame({"trend": trend, "vol": vol}, index=market_close.index)


def ic_by_regime(feature: pd.DataFrame, fwd_ret: pd.DataFrame,
                 regimes: pd.DataFrame, dimension: str = "trend") -> pd.DataFrame:
    """レジーム区分ごとのIC平均・IR・観測数を返す。"""
    ic = evaluation.ic_series(feature, fwd_ret)
    reg = regimes[dimension].reindex(ic.index)
    rows = []
    for label in pd.unique(reg.dropna()):
        sub = ic[reg == label]
        s = evaluation.ic_summary(sub)
        rows.append({
            "regime": label, "n": s.get("n", 0),
            "ic_mean": s.get("ic_mean", np.nan), "ic_ir": s.get("ic_ir", np.nan),
        })
    return pd.DataFrame(rows).sort_values("regime").reset_index(drop=True)
