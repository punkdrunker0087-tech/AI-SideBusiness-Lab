"""4. 評価 ―― Information Coefficient(IC)で予測力を測る（価格ベースのみ）。

⚠️ Value/Quality/Sizeはスナップショットのみのため、時系列ICでの正式な
予測力評価はできない（過去に一律適用すると先読みバイアス）。ここでの
IC評価は Momentum・LowVol の**価格ベース・全期間ファクター専用**。
Value/Quality/Sizeは `exposure.py` のライブ・エクスポージャー分析でのみ扱う。
"""
import numpy as np
import pandas as pd
from scipy import stats


def forward_return(close: pd.DataFrame, horizon: int = 20) -> pd.DataFrame:
    return close.shift(-horizon) / close - 1


def ic_series(feature: pd.DataFrame, fwd_ret: pd.DataFrame) -> pd.Series:
    """各時点の銘柄横断 Spearman IC。"""
    f, r = feature.align(fwd_ret, join="inner")
    out = {}
    for t in f.index:
        pair = pd.concat([f.loc[t], r.loc[t]], axis=1).dropna()
        if len(pair) < 5:
            continue
        x, y = pair.iloc[:, 0], pair.iloc[:, 1]
        if x.nunique() < 3 or y.nunique() < 3:
            continue
        c = stats.spearmanr(x, y).correlation
        if not np.isnan(c):
            out[t] = c
    return pd.Series(out, name="IC")


def ic_summary(ic: pd.Series) -> dict:
    ic = ic.dropna()
    n = len(ic)
    if n < 2:
        return {"n": n, "ic_mean": np.nan, "ic_ir": np.nan, "hit_rate": np.nan, "t_stat": np.nan}
    mean, sd = ic.mean(), ic.std(ddof=1)
    ir = mean / sd if sd else np.nan
    t = mean / (sd / np.sqrt(n)) if sd else np.nan
    return {"n": n, "ic_mean": float(mean), "ic_ir": float(ir),
            "hit_rate": float((ic > 0).mean()), "t_stat": float(t)}


def evaluate_price_factor(feature: pd.DataFrame, close: pd.DataFrame,
                          horizon: int = 20) -> dict:
    fwd = forward_return(close, horizon)
    return ic_summary(ic_series(feature, fwd))
