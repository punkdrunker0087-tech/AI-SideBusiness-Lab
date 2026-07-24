"""ペア候補の探索 ―― 同一業種・類似事業構造・流動性・データ品質から絞り込む。

相関だけでは長期的な関係性があるとは限らないため、ここでは「候補の一次
スクリーニング」に留め、本当に安定した関係かはStage3(cointegration.py)で
検定する。相関はスクリーニングの入口に過ぎない。
"""
import numpy as np
import pandas as pd


def candidate_pairs(close: pd.DataFrame, volume: pd.DataFrame, sectors: pd.Series,
                    min_corr: float = 0.5, min_avg_dollar_volume: float = 1e8) -> pd.DataFrame:
    """同一業種・最低流動性・最低相関を満たすペア候補を列挙する。

    min_avg_dollar_volume: 平均売買代金の下限（円）。流動性の低い銘柄は
    ペアトレードの執行コストが高くつくため除外する。
    """
    ret = close.pct_change().dropna()
    dollar_vol = (close * volume).mean()

    rows = []
    symbols = list(close.columns)
    for i, a in enumerate(symbols):
        for b in symbols[i + 1:]:
            if sectors.get(a) != sectors.get(b) or sectors.get(a) == "不明":
                continue
            if dollar_vol.get(a, 0) < min_avg_dollar_volume or dollar_vol.get(b, 0) < min_avg_dollar_volume:
                continue
            common = ret[[a, b]].dropna()
            if len(common) < 60:
                continue
            corr = common[a].corr(common[b])
            # データ品質: 欠損率
            missing_rate = close[[a, b]].isna().mean().mean()
            rows.append({
                "銘柄A": a, "銘柄B": b, "業種": sectors.get(a),
                "相関": corr, "平均売買代金A(億円)": dollar_vol[a] / 1e8,
                "平均売買代金B(億円)": dollar_vol[b] / 1e8, "欠損率": missing_rate,
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df[df["相関"] >= min_corr].sort_values("相関", ascending=False).reset_index(drop=True)
