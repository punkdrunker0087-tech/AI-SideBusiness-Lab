"""相関と分散 ―― ファクター同士の関係は時間とともに変化する。

2種類の相関を区別して扱う:
  1. **ファクターリターンの時系列相関**（Momentum・LowVolなど価格ベースの
     ファクターのみ。全期間で先読みなく構築できるため正式に評価可能）
  2. **現時点でのファクター・スコアの横断相関**（Value/Quality/Size含む全5
     ファクター。スナップショットなので「今日、銘柄選択がどれだけ重複するか」
     の目安に留まり、時系列の関係ではない）
"""
import numpy as np
import pandas as pd


def rebalance_dates(index: pd.DatetimeIndex, freq: str) -> list:
    """各期間の *実際の最終取引日* を返す。

    `index.resample(freq).last().index` は期間末の暦日ラベル（例: 1/31）を
    返すため、それが土日祝で取引日でなければ `in index` 判定に失敗し
    リバランスが黙って抜け落ちる（週次で全滅することもある）。
    日付そのものをresampleして値（=実際の取引日）を取ることで回避する。
    """
    s = pd.Series(index, index=index)
    return s.resample(freq).last().dropna().tolist()


def factor_return_series(feature: pd.DataFrame, close: pd.DataFrame,
                         rebalance: str = "ME", q: int = 5) -> pd.Series:
    """特徴量の上位分位−下位分位（ロング・ショート）の日次リターン系列。

    先読み防止: リバランス日の特徴量で銘柄選定し、翌営業日以降のリターンに適用。
    """
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
    return (held * ret).sum(axis=1)


def factor_return_correlation(factor_returns: dict, window: int = 60) -> pd.DataFrame:
    """ファクターリターン間のローリング相関の平均・推移サマリ。"""
    df = pd.DataFrame(factor_returns).dropna()
    full_corr = df.corr()

    # 直近window日 vs それ以前の相関（時間変化の粗い確認）
    if len(df) > window * 2:
        recent = df.iloc[-window:].corr()
        earlier = df.iloc[:-window].corr()
    else:
        recent = earlier = full_corr

    names = list(factor_returns)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            rows.append({
                "ペア": f"{a} × {b}",
                "全期間相関": full_corr.loc[a, b],
                "直近相関": recent.loc[a, b],
                "以前の相関": earlier.loc[a, b],
                "変化": recent.loc[a, b] - earlier.loc[a, b],
            })
    return pd.DataFrame(rows)


def cross_sectional_factor_correlation(factor_z_today: pd.DataFrame) -> pd.DataFrame:
    """現時点の5ファクター・スコア間の横断相関（銘柄選択の重複度）。"""
    return factor_z_today.corr()


def stress_correlation(factor_returns: dict, market_ret: pd.Series,
                       stress_quantile: float = 0.1) -> pd.DataFrame:
    """市場が大きく下げた日 vs 平常時で、ファクター間相関がどう変わるか。"""
    df = pd.DataFrame(factor_returns).join(market_ret.rename("_mkt"), how="inner").dropna()
    thr = df["_mkt"].quantile(stress_quantile)
    stress = df[df["_mkt"] <= thr].drop(columns="_mkt")
    calm = df[df["_mkt"] > thr].drop(columns="_mkt")

    names = list(factor_returns)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            c_calm = calm[a].corr(calm[b]) if len(calm) > 5 else np.nan
            c_stress = stress[a].corr(stress[b]) if len(stress) > 5 else np.nan
            rows.append({"ペア": f"{a} × {b}", "平常時": c_calm, "ストレス時": c_stress,
                        "変化": (c_stress - c_calm) if pd.notna(c_stress) and pd.notna(c_calm) else np.nan})
    return pd.DataFrame(rows)
