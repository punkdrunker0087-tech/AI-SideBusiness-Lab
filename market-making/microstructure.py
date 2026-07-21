"""マイクロストラクチャー指標 ―― 実データからの代理指標＋シミュレーション指標。

⚠️ 無料の日次OHLCVには板情報（気配・出来高の内訳）がないため、
「板の厚さ」「注文キャンセル率」「注文フローの偏り」はシミュレーション
（`simulation.py`）でのみ厳密に扱える。ここでは日次データから計算できる
**代理指標**（Rollの実効スプレッド推定量・Amihud非流動性）を実装し、
その限界を明示する。

参照:
  Roll, R. (1984) "A Simple Implicit Measure of the Bid-Ask Spread"
  Amihud, Y. (2002) "Illiquidity and Stock Returns"
"""
import numpy as np
import pandas as pd


def roll_spread_estimate(close: pd.Series, window: int = 20) -> pd.Series:
    """Rollの実効スプレッド推定量: 2√(−Cov(ΔP_t, ΔP_{t-1}))。

    価格変化の負の系列相関（買い→売りの跳ね返り）からスプレッドを逆算する。
    共分散が正の場合（トレンド優勢）は推定不能としてNaNを返す。
    """
    dp = close.diff()
    cov = dp.rolling(window).apply(
        lambda x: np.cov(x[:-1], x[1:])[0, 1] if len(x) > 2 else np.nan, raw=True
    )
    spread = 2 * np.sqrt((-cov).clip(lower=0))
    spread[cov > 0] = np.nan
    return spread


def amihud_illiquidity(close: pd.Series, volume: pd.Series, window: int = 20) -> pd.Series:
    """Amihud非流動性: 平均( |日次リターン| / 売買代金 )。大きいほど非流動的
    （少ない出来高で価格が動きやすい＝マーケットメイクのリスクが高い）。
    """
    ret = close.pct_change().abs()
    dollar_vol = (close * volume).replace(0, np.nan)
    illiq = ret / dollar_vol
    # 日本の大型株は売買代金(円)が非常に大きいため、無調整だと1e-12オーダーになる。
    # 1e6倍しても値自体は小さいまま(銘柄間の相対比較には支障なし)。
    return illiq.rolling(window).mean() * 1e6


def realized_volatility(close: pd.Series, window: int = 20, periods: int = 252) -> pd.Series:
    """実現ボラティリティ（年率）。クォートのスプレッド・在庫リスクの入力になる。"""
    logret = np.log(close / close.shift(1))
    return logret.rolling(window).std() * np.sqrt(periods)


def summary(close: pd.Series, volume: pd.Series) -> dict:
    roll = roll_spread_estimate(close)
    amihud = amihud_illiquidity(close, volume)
    rv = realized_volatility(close)
    return {
        "roll_spread_mean": float(roll.dropna().mean()) if roll.notna().any() else np.nan,
        "roll_spread_estimable_pct": float(roll.notna().mean()),
        "amihud_illiquidity_mean": float(amihud.dropna().mean()) if amihud.notna().any() else np.nan,
        "realized_vol_mean": float(rv.dropna().mean()),
    }
