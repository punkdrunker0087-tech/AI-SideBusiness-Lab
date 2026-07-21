"""3. 特徴量設計 ―― 時点ごとに利用可能な情報だけで特徴量を作る。

すべて `rolling`/`shift` のみで実装し、将来のデータを参照しない
（`data_prep.assert_no_future_leakage` で自動検証できる設計）。
"""
import numpy as np
import pandas as pd


def momentum(close: pd.DataFrame, lookback: int = 120) -> pd.DataFrame:
    return close / close.rolling(lookback).mean() - 1


def volatility(close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    logret = np.log(close / close.shift(1))
    return logret.rolling(window).std() * np.sqrt(252)


def liquidity(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    return np.log((close * volume).replace(0, np.nan))


def reversal(close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    return close / close.shift(window) - 1


def rsi(close: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


FEATURE_BUILDERS = {
    "momentum_120": lambda close, volume=None: momentum(close, 120),
    "volatility_20": lambda close, volume=None: volatility(close, 20),
    "reversal_5": lambda close, volume=None: reversal(close, 5),
    "rsi_14": lambda close, volume=None: rsi(close, 14),
}


def cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, np.nan), axis=0)


def build_dataset(close: pd.DataFrame, volume: pd.DataFrame, horizon: int = 20) -> pd.DataFrame:
    """(date, symbol)を行とする長形式データセットを作る。

    特徴量は各日クロスセクションZスコア化（銘柄横断で比較可能にする）。
    ラベルは horizon 日先の相対リターン順位（0〜1・銘柄横断のパーセンタイル）。
    ラベルが計算できない直近 horizon 日分は自動的にNaNになり、後で除外する。
    """
    feats_z = {}
    for name, fn in FEATURE_BUILDERS.items():
        raw = fn(close, volume) if "liquidity" not in name else liquidity(close, volume)
        feats_z[name] = cross_sectional_zscore(raw)
    feats_z["liquidity_log"] = cross_sectional_zscore(liquidity(close, volume))

    fwd_ret = close.shift(-horizon) / close - 1
    label_rank = fwd_ret.rank(axis=1, pct=True)  # 0〜1（銘柄横断パーセンタイル）

    frames = []
    for name, panel in feats_z.items():
        frames.append(panel.stack(future_stack=True).rename(name))
    X = pd.concat(frames, axis=1)
    y = label_rank.stack(future_stack=True).rename("label")

    df = pd.concat([X, y], axis=1)
    df.index.names = ["date", "symbol"]
    return df.reset_index()
