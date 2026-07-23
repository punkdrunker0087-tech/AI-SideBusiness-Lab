"""短期リバーサル・アイディオシンクラティック・ボラティリティ ―― 「第3の情報軸」候補。

ユーザーの整理: 現有5ファクターは実質2テーマ（A=マクロ/リスクオン軸
[FX・Rate・符号反転LowVol]、B=価格テクニカル軸[Momentum・Liquidity]）
しかない。次に探すべきは、この2テーマとは異なる**独立した情報源**。

学術的に12ヶ月モメンタムとは別の現象とされる**短期リバーサル**（1ヶ月
リターンの平均回帰、Jegadeesh 1990）と、**アイディオシンクラティック・
ボラティリティ**（市場ベータ除去後の残差ボラ、Ang, Hodrick, Xing &
Zhang 2006の「低IVOLアノマリー」）の2つを実装する。

⚠️ IVOLは推定窓に結果が大きく依存することが知られているため、
DSR/PBOでの検証が必須（ユーザー指摘）。
"""
import numpy as np
import pandas as pd

import factors


def reversal_score(close: pd.DataFrame, window: int = 21) -> pd.DataFrame:
    """短期リバーサル: 直近window日の累積リターンの逆符号を横断Zスコア化。

    高いスコア=直近下落した銘柄（平均回帰で反発が期待される、というのが
    学術的な仮説）。12ヶ月モメンタム（`factors.momentum`）とは異なる
    ホライズンの現象として、符号も逆（モメンタムは「上がった株を買う」、
    リバーサルは「下がった株を買う」）。
    """
    short_term_return = close / close.shift(window) - 1
    return factors.zscore_cross(-short_term_return)


def idiosyncratic_vol_score(close: pd.DataFrame, market_ret: pd.Series,
                            window: int = 60) -> pd.DataFrame:
    """アイディオシンクラティック・ボラティリティ: 市場ベータ除去後の
    残差リターンの標準偏差を横断Zスコア化（符号は経験的に決定、下記参照）。

    Ang et al. (2006)の「低IVOLアノマリー」に従えば、低IVOL銘柄が
    相対的に高いリターンを持つとされる。ただし符号を仮定せず、
    実際に標準スコア(高IVOL=高スコア)とその逆(低IVOL=高スコア)の
    両方を単独バックテストし、どちらが正のSharpeを示すかで判断する
    （`factor_gate_evaluation.py`参照。事後的な符号選びである点は
    正直に明記する）。
    """
    stock_ret = close.pct_change()
    mkt = market_ret.reindex(close.index)
    beta = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)
    mkt_var = mkt.rolling(window).var()
    for col in close.columns:
        cov = stock_ret[col].rolling(window).cov(mkt)
        beta[col] = cov / mkt_var
    residual = stock_ret.sub(beta.mul(mkt, axis=0))
    ivol = residual.rolling(window).std()
    return factors.zscore_cross(ivol)
