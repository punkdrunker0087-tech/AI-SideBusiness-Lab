"""売買シグナル（ポジション）を生成する戦略群。

各関数は OHLCV の DataFrame を受け取り、各日のポジションを表す Series を返す。
ポジションは close[t] の時点で決定され、翌日 close[t+1] のリターンに適用される
（先読みバイアスを避けるため、バックテスト側で1日ずらす）。

値の意味: 1.0 = フルロング, 0.0 = ノーポジション（現金）
（信用売りを使わない前提でロングのみ。空売り対応時は -1.0 も許容できる）
"""
import numpy as np
import pandas as pd


def buy_hold(df: pd.DataFrame) -> pd.Series:
    """常時フルロング。すべての戦略が最低限これを上回る必要がある基準線。"""
    return pd.Series(1.0, index=df.index)


def sma_crossover(df: pd.DataFrame, fast: int = 25, slow: int = 75) -> pd.Series:
    """短期移動平均が長期を上回っている間ロング（トレンド追随）。"""
    close = df["close"]
    fast_ma = close.rolling(fast).mean()
    slow_ma = close.rolling(slow).mean()
    return (fast_ma > slow_ma).astype(float)


def momentum(df: pd.DataFrame, lookback: int = 60) -> pd.Series:
    """過去lookback日で上昇していればロング（時系列モメンタム）。"""
    close = df["close"]
    return (close / close.shift(lookback) - 1 > 0).astype(float)


def rsi_reversion(
    df: pd.DataFrame, period: int = 14, low: float = 30.0, high: float = 70.0
) -> pd.Series:
    """RSIが売られすぎ(low)でロング、買われすぎ(high)で手仕舞い（逆張り）。"""
    close = df["close"]
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)

    pos = pd.Series(np.nan, index=close.index)
    pos[rsi < low] = 1.0
    pos[rsi > high] = 0.0
    return pos.ffill().fillna(0.0)


REGISTRY = {
    "buy_hold": buy_hold,
    "sma_crossover": sma_crossover,
    "momentum": momentum,
    "rsi_reversion": rsi_reversion,
}
