"""ファクター計算とクロスセクショナルZスコア。

すべて価格・出来高のみから計算する（Qualityは財務データが必要なため未実装）。
先読み防止のため、各ファクターは時点tまでの情報だけで計算される
（rolling系はその性質上、未来を参照しない）。
"""
import numpy as np
import pandas as pd


def momentum(close: pd.DataFrame, lookback: int = 120) -> pd.DataFrame:
    """M = P_t / SMA_120 − 1（中期トレンド）。"""
    return close / close.rolling(lookback).mean() - 1


def volatility(close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """σ = sqrt(252) × std(日次対数リターン, 20日)。"""
    logret = np.log(close / close.shift(1))
    return logret.rolling(window).std() * np.sqrt(252)


def liquidity(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """L = log(Volume × Price)（売買代金の対数）。"""
    return np.log((volume * close).replace(0, np.nan))


def zscore_cross(df: pd.DataFrame) -> pd.DataFrame:
    """各日（行）について、銘柄横断（列方向）のZスコアを計算する。"""
    mean = df.mean(axis=1)
    std = df.std(axis=1)
    return df.sub(mean, axis=0).div(std.replace(0, np.nan), axis=0)


# Quality は財務データ（ROE・粗利率・資本集約度）が必要で、無料経路では
# 取得できないため未実装。取得できるようになったら下記シグネチャで追加する:
#   def quality(fundamentals) -> pd.DataFrame: ...
