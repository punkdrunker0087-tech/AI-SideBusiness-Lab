"""4. シグナル評価 ―― Information Coefficient(IC) を中心に予測力を測る。

IC = 各時点で「特徴量(横断)」と「将来リターン(横断)」の相関。
  IC_t = corr( feature[t, :] , forward_return[t, :] )  （銘柄横断）
  Rank IC は Spearman（順位相関）で外れ値に頑健。

指標:
  - ic_series      : ICの時系列
  - ic_summary     : IC平均・標準偏差・IC情報比(IR=mean/std)・勝率・t値
  - ic_decay       : ホライズン別ICの減衰
  - quantile_spread: 上位分位 − 下位分位 の将来平均リターン
"""
import numpy as np
import pandas as pd
from scipy import stats


def ic_series(feature: pd.DataFrame, fwd_ret: pd.DataFrame, rank: bool = True) -> pd.Series:
    """各時点の銘柄横断IC。rank=TrueでSpearman(順位IC)。"""
    f, r = feature.align(fwd_ret, join="inner")
    out = {}
    for t in f.index:
        a, b = f.loc[t], r.loc[t]
        pair = pd.concat([a, b], axis=1).dropna()
        if len(pair) < 5:
            continue
        x, y = pair.iloc[:, 0], pair.iloc[:, 1]
        if x.nunique() < 3 or y.nunique() < 3:
            continue
        c = stats.spearmanr(x, y).correlation if rank else np.corrcoef(x, y)[0, 1]
        if not np.isnan(c):
            out[t] = c
    return pd.Series(out, name="IC")


def ic_summary(ic: pd.Series) -> dict:
    """ICの要約統計。IR = mean/std（1に近いほど安定して効く）。"""
    ic = ic.dropna()
    n = len(ic)
    if n < 2:
        return {"n": n}
    mean, sd = ic.mean(), ic.std(ddof=1)
    ir = mean / sd if sd else np.nan
    tstat = mean / (sd / np.sqrt(n)) if sd else np.nan
    return {
        "n": n,
        "ic_mean": float(mean),
        "ic_std": float(sd),
        "ic_ir": float(ir),
        "hit_rate": float((ic > 0).mean()),
        "t_stat": float(tstat),
    }


def ic_decay(feature: pd.DataFrame, close: pd.DataFrame,
             horizons=(1, 2, 3, 5, 10, 20, 40)) -> pd.DataFrame:
    """ホライズン別のIC平均（効果がどの時間軸で最も強く、いつ減衰するか）。"""
    import features as ft

    rows = []
    for h in horizons:
        fwd = ft.forward_return(close, h)
        s = ic_summary(ic_series(feature, fwd))
        rows.append({"horizon": h, "ic_mean": s.get("ic_mean", np.nan),
                     "ic_ir": s.get("ic_ir", np.nan)})
    return pd.DataFrame(rows)


def quantile_spread(feature: pd.DataFrame, fwd_ret: pd.DataFrame, q: int = 5) -> dict:
    """特徴量で分位に分け、上位分位 − 下位分位 の将来平均リターン。"""
    f, r = feature.align(fwd_ret, join="inner")
    top, bot = [], []
    for t in f.index:
        pair = pd.concat([f.loc[t], r.loc[t]], axis=1).dropna()
        if len(pair) < q * 2:
            continue
        pair.columns = ["feat", "ret"]
        ranks = pair["feat"].rank(pct=True)
        top.append(pair.loc[ranks > 1 - 1 / q, "ret"].mean())
        bot.append(pair.loc[ranks < 1 / q, "ret"].mean())
    top, bot = np.array(top), np.array(bot)
    spread = np.nanmean(top - bot)
    return {
        "top_mean_ret": float(np.nanmean(top)),
        "bottom_mean_ret": float(np.nanmean(bot)),
        "spread": float(spread),
        "n_periods": len(top),
    }
