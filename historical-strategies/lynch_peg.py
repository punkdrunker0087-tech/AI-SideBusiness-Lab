"""Peter Lynch の PEG レシオ ―― *One Up on Wall Street* (1989)。

## ①原典 / ②公式の要約
Lynchは「成長率に対して株価が割安かどうか」を一目で判断する指標として
PEG（Price/Earnings to Growth）を広めた（原典では"P/E to growth rate"と
表現、後年PEGという呼称が定着）:

  PEG = PER(P/E) / 利益成長率(%を数値のまま、例: 25%成長なら25)

Lynchの目安（原典の記述の要旨）:
  - PEG ≈ 1 が「フェアバリュー」
  - PEG < 1 は割安（成長の割に株価が安い）
  - PEG > 1.5〜2 は割高、避けるべき

Lynchは"fast growers"（年20〜25%以上成長する中小型株）を好み、
PEGはその中で「成長を買いすぎていないか」を測るフィルターとして使った。

## ③④ 現代データへの数式化
  PEG = trailing_pe / (earnings_growth × 100)

⚠️ earnings_growth が0以下（減益・赤字転換）の銘柄はPEGが定義できない
（分母が0以下になり符号が反転し無意味な値になる）。原典もそもそも
"growth"株を対象とした指標であり、減益企業への適用は想定外。
本実装ではこれらを明示的に除外し、無意味な値が紛れ込まないようにする。
"""
import numpy as np
import pandas as pd


def compute_peg(fundamentals: pd.DataFrame, min_growth_pct: float = 0.1) -> pd.DataFrame:
    """PEGレシオを計算し、Lynchの目安に沿って分類する。

    min_growth_pct: 成長率がこの値（例: 0.1 = 10%）未満の銘柄はPEGの
    前提（fast grower）から外れるため除外する。0にすると原典の趣旨を
    外れた「ほぼ無成長企業へのPEG適用」という危険なケースを再現できる。
    """
    df = fundamentals.copy()
    df["trailing_pe"] = pd.to_numeric(df["trailing_pe"], errors="coerce")
    df["earnings_growth"] = pd.to_numeric(df["earnings_growth"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["trailing_pe", "earnings_growth"])
    df = df[df["trailing_pe"] > 0]
    excluded_low_growth = int((df["earnings_growth"] < min_growth_pct).sum())
    df = df[df["earnings_growth"] >= min_growth_pct]

    df["peg"] = df["trailing_pe"] / (df["earnings_growth"] * 100)

    def classify(peg):
        if peg < 1.0:
            return "割安(<1)"
        if peg <= 1.5:
            return "フェアバリュー(1〜1.5)"
        if peg <= 2.0:
            return "やや割高(1.5〜2)"
        return "割高・回避(>2)"

    df["判定"] = df["peg"].apply(classify)
    df = df.sort_values("peg")
    df.attrs["n_excluded_total"] = before - len(df)
    df.attrs["n_excluded_low_growth"] = excluded_low_growth
    return df
