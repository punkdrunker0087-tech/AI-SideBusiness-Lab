"""George Soros のリフレクシビティ理論 ―― *The Alchemy of Finance* (1987)。

## ①原典 / ②論文調査の要約
Sorosの中心的主張は、市場では2つの機能が同時に働くというもの:

  - **認知機能**（cognitive function）: 参加者が価格・ファンダメンタルズ
    から見解（bias）を形成する（現実→認識）
  - **参加機能**（participative function）: その見解に基づいて売買し、
    見ようとしていたファンダメンタルズそのものを変えてしまう（認識→現実）

この2つの機能が正のフィードバックループを形成すると、ブーム・バスト
（boom-bust）が発生する。ブームは緩やかに加速しながら長く続き、バストは
（投げ売りに増幅されて）短く急峻、という非対称性が特徴（Soros自身・
及び後年の学術的解説（macro-ops.com, arxiv:0901.4447の力学系分析）でも
共通して指摘されている）。

Soros自身も「Knightian不確実性は定量化できないが、トレンドの存在や
転換自体は定量化せずとも識別できる」「支配的バイアス（prevailing bias）
は実際のPERと長期平均PERの乖離として測定できる」と述べている
（georgesoros.com "Fallibility, Reflexivity..."）。

## ③④ 現代データへの数式化（代理指標・要注意）
⚠️ Sorosが例示するPER乖離は、本シリーズの他戦略同様、Yahooのライブ
スナップショットPERしか使えず、時系列としての「その時点のPERの長期
平均からの乖離」を再現できない（点in-timeの実績PER時系列が必要だが
無料データでは入手不可）。

そこで本実装では、**価格の時系列だけで先読みなく計算できる代理指標**に
切り替える:

  - 支配的バイアス（bias）の代理 = 価格の長期移動平均からの乖離率
    `bias(t) = (P(t) − MA_long(t)) / MA_long(t)`
  - フィードバックの強さ（自己強化度）の代理 = モメンタムの変化率
    （モメンタム自体が加速しているか減速しているか）
    `accel(t) = momentum(t) − momentum(t − lag)`

この2軸で4象限に分類する:
  - **ブーム加速**: bias>0 かつ accel>0（トレンドが自己強化中）
  - **黄昏期(twilight)**: bias>0 だが accel<0（高値圏で勢いが鈍化＝
    Sorosの言う「ブームの終盤、バストの予兆」）
  - **バスト**: bias<0 かつ accel<0
  - **回復**: bias<0 だが accel>0

Sorosの理論の実践的含意は「ブーム加速期はトレンドに乗り、黄昏期
（勢いの鈍化）で手仕舞う」という非対称な出口設計にある（バストは急峻
なので、ピークでの正確な予測より早期の手仕舞いを優先する）。
"""
import numpy as np
import pandas as pd


def compute_bias(close: pd.Series, long_window: int = 200) -> pd.Series:
    ma_long = close.rolling(long_window).mean()
    return (close - ma_long) / ma_long


def compute_momentum(close: pd.Series, window: int = 63) -> pd.Series:
    return close / close.shift(window) - 1


def compute_acceleration(momentum: pd.Series, lag: int = 21) -> pd.Series:
    return momentum - momentum.shift(lag)


def classify_regime(bias: pd.Series, accel: pd.Series) -> pd.Series:
    regime = pd.Series(index=bias.index, dtype=object)
    regime[(bias > 0) & (accel > 0)] = "ブーム加速"
    regime[(bias > 0) & (accel <= 0)] = "黄昏期"
    regime[(bias <= 0) & (accel <= 0)] = "バスト"
    regime[(bias <= 0) & (accel > 0)] = "回復"
    return regime


def backtest_reflexivity_rule(close: pd.Series, long_window: int = 200,
                              mom_window: int = 63, accel_lag: int = 21) -> dict:
    """「ブーム加速・回復ではロング、黄昏期・バストではフラット」というルールを検証する。

    全て過去データのみで計算されるローリング指標なので、先読みバイアスはない
    （シグナルはt日終値で確定、ポジションはt+1日から反映）。
    """
    bias = compute_bias(close, long_window)
    momentum = compute_momentum(close, mom_window)
    accel = compute_acceleration(momentum, accel_lag)
    regime = classify_regime(bias, accel)

    position = regime.isin(["ブーム加速", "回復"]).astype(float)
    position = position.shift(1).fillna(0.0)

    ret = close.pct_change().fillna(0.0)
    strat_ret = position * ret
    equity = (1 + strat_ret).cumprod()
    bh_equity = close / close.iloc[0]

    return {
        "bias": bias, "accel": accel, "regime": regime,
        "position": position, "equity": equity, "bh_equity": bh_equity,
        "final_multiple": float(equity.iloc[-1]),
        "bh_final_multiple": float(bh_equity.iloc[-1]),
        "regime_counts": regime.value_counts(),
    }
