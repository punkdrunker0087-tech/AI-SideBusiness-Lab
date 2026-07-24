"""ベクトル型 vs イベント駆動型エンジンの設計比較（最小実装）。

- **ベクトル型**: 全時点のシグナルを配列演算で一括計算。高速・簡潔だが、
  「建玉に依存する損切り」など経路依存の執行を表現しづらく、先読みも混入しやすい。
- **イベント駆動型**: 時点を1本ずつ進め、状態（現金・建玉・約定）を更新。
  低速だが現実の執行（ストップ・部分約定・遅延）を忠実に表現でき、先読みしにくい。

同じSMAクロス戦略を両方で実装し、結果が一致することと、イベント駆動型だけが
表現できる要素（ATRストップ）を示す。
"""
import numpy as np
import pandas as pd


def signals_sma(close: pd.Series, fast: int = 20, slow: int = 60) -> pd.Series:
    """SMA(fast) > SMA(slow) の間ロング（1/0）。"""
    return (close.rolling(fast).mean() > close.rolling(slow).mean()).astype(float)


def vectorized(close: pd.Series, positions: pd.Series, cost_bps: float = 15.0) -> pd.Series:
    """ベクトル型: リターン = 前日建玉 × 当日リターン − コスト。返り値はエクイティ。"""
    ret = close.pct_change().fillna(0.0)
    held = positions.shift(1).fillna(0.0)          # 先読み防止
    turnover = positions.diff().abs().fillna(positions.abs())
    net = held * ret - turnover * (cost_bps / 1e4)
    return (1 + net).cumprod()


def event_driven(close: pd.Series, fast: int = 20, slow: int = 60,
                 cost_bps: float = 15.0, atr_stop: float = None,
                 atr_window: int = 14) -> pd.Series:
    """イベント駆動型: 1本ずつ進めて建玉と現金を更新。

    atr_stop を指定すると、建玉中に価格が (エントリー − atr_stop×ATR) を割ったら
    強制手仕舞い（＝経路依存の執行。ベクトル型では書きづらい）。
    """
    sma_f = close.rolling(fast).mean()
    sma_s = close.rolling(slow).mean()
    atr = (close.diff().abs()).rolling(atr_window).mean()  # 簡易ATR（日次値幅の平均）

    equity = 1.0
    position = 0        # 0 or 1
    entry_price = None
    curve = []
    prices = close.values
    for i in range(len(close)):
        px = prices[i]
        prev = prices[i - 1] if i > 0 else px
        # 建玉があれば当日の値動きを反映
        if position == 1 and prev:
            equity *= 1 + (px / prev - 1)

        # --- 執行判断（当日終値の確定情報のみ使う→翌日反映で先読み回避） ---
        signal_long = (sma_f.iloc[i] > sma_s.iloc[i]) if not np.isnan(sma_s.iloc[i]) else False

        # ATRストップ（経路依存）: 建玉中に割れたら手仕舞い
        if position == 1 and atr_stop and entry_price and not np.isnan(atr.iloc[i]):
            if px < entry_price - atr_stop * atr.iloc[i]:
                signal_long = False

        target = 1 if signal_long else 0
        if target != position:
            equity *= 1 - cost_bps / 1e4          # 売買コスト
            if target == 1:
                entry_price = px
            else:
                entry_price = None
            position = target
        curve.append(equity)

    return pd.Series(curve, index=close.index)
