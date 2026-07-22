"""William O'Neil の CAN SLIM ―― *How to Make Money in Stocks* (1988)。

## ①原典 / ②公式の要約
7つの頭文字から成る、成長株を見つけるためのチェックリスト:

  C = Current quarterly earnings（直近四半期EPS成長率、目安+25%以上）
  A = Annual earnings growth（過去3年の年間EPS成長率、目安+25%以上、
      加えてROE 17%以上が望ましいとされる）
  N = New products/New highs（新製品・新高値更新、株価が52週高値に近いこと）
  S = Supply and demand（出来高。株価上昇時に出来高が増える＝需要超過の証拠）
  L = Leader or laggard（相対的な値動きの強さ。業界内でトップクラスの銘柄）
  I = Institutional sponsorship（機関投資家の保有比率上昇）
  M = Market direction（市場全体のトレンド。上昇トレンドでなければ
      個別銘柄がいくら良くても新規建玉は避ける、というマクロフィルター）

## ③④ 現代データへの数式化（近似・要注意）
Yahoo Financeの`earningsQuarterlyGrowth`は無料APIで欠損することが多い
（実装時の検証で本ユニバースの銘柄でNoneだった）。そのため**C（四半期
成長率）はA同様に`earningsGrowth`（年間ベース）で代用する**近似とし、
その旨を明記する。各項目の数式:

  C_proxy = earnings_growth（本来は四半期、年間成長率で代用）
  A       = earnings_growth（年間）+ ROE
  N       = 直近終値 / 直近52週高値（1に近いほど良い）
  S       = 直近20日平均出来高 / 直近120日平均出来高（>1で出来高増加）
  L       = 対ベンチマークの相対強度（直近6ヶ月リターン差）
  I       = held_pct_institutions（機関投資家保有比率）
  M       = ベンチマークが自身の200日移動平均を上回っているか（ゲート条件）

原典のMは「市場が弱気なら新規建玉を避ける」というゲート（フィルター）
であり、他6項目のような加点スコアではない。本実装もその通りに、
Mはスコアには含めず、別途「今は新規エントリーに適した地合いか」という
真偽値として扱う。
"""
import numpy as np
import pandas as pd


def compute_canslim(fundamentals: pd.DataFrame, close: pd.DataFrame,
                    volume: pd.DataFrame, bench: pd.Series) -> pd.DataFrame:
    """C/A/N/S/L/Iの複合スコアと、Mのゲート判定を計算する。

    close, volume: 銘柄×日付のDataFrame（fundamentals.indexと同じ銘柄を含む）
    bench: ベンチマークの終値Series（closeと同じ日付インデックス）
    """
    symbols = fundamentals.index.tolist()
    df = fundamentals.copy()
    df["earnings_growth"] = pd.to_numeric(df["earnings_growth"], errors="coerce")
    df["roe"] = pd.to_numeric(df["roe"], errors="coerce")
    df["held_pct_institutions"] = pd.to_numeric(df["held_pct_institutions"], errors="coerce")

    last = close.iloc[-1]
    high_52w = close.iloc[-252:].max() if len(close) >= 252 else close.max()
    df["N_price_vs_52w_high"] = (last / high_52w)[symbols]

    vol_short = volume.iloc[-20:].mean()
    vol_long = volume.iloc[-120:].mean() if len(volume) >= 120 else volume.mean()
    df["S_volume_ratio"] = (vol_short / vol_long)[symbols]

    stock_6m_ret = close.iloc[-1] / close.iloc[-126] - 1 if len(close) >= 126 else close.iloc[-1] / close.iloc[0] - 1
    bench_6m_ret = bench.iloc[-1] / bench.iloc[-126] - 1 if len(bench) >= 126 else bench.iloc[-1] / bench.iloc[0] - 1
    df["L_relative_strength"] = (stock_6m_ret[symbols] - bench_6m_ret)

    df["C_proxy_quarterly_growth"] = df["earnings_growth"]
    df["A_annual_growth"] = df["earnings_growth"]
    df["I_institutional_pct"] = df["held_pct_institutions"]

    rank_cols = {
        "C_proxy_quarterly_growth": False,
        "A_annual_growth": False,
        "N_price_vs_52w_high": False,
        "S_volume_ratio": False,
        "L_relative_strength": False,
        "I_institutional_pct": False,
    }
    rank_sum = pd.Series(0.0, index=df.index)
    n_ranked = 0
    for col, ascending in rank_cols.items():
        r = df[col].rank(ascending=ascending, na_option="bottom")
        rank_sum = rank_sum.add(r, fill_value=r.max())
        n_ranked += 1
    df["combined_rank"] = rank_sum

    df = df.sort_values("combined_rank")

    bench_ma200 = bench.rolling(200).mean().iloc[-1] if len(bench) >= 200 else bench.mean()
    m_gate_bullish = bool(bench.iloc[-1] > bench_ma200)
    df.attrs["M_market_uptrend"] = m_gate_bullish
    return df
