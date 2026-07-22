"""Feature Pipeline ―― 特徴量生成・バージョン管理・再現性確保。

特徴量はすべて過去データのみで計算し（先読みなし）、元データのハッシュ・
計算方法・バージョンを記録することで、後から同じ条件で再現できるようにする。
"""
import hashlib

import numpy as np
import pandas as pd

import event_log

VERSION = "v1"


def _hash_series(s: pd.Series) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(s, index=True).values.tobytes()).hexdigest()[:16]


def momentum(close: pd.Series, lookback: int = 20) -> pd.Series:
    return close / close.rolling(lookback).mean() - 1


def volatility(close: pd.Series, window: int = 20) -> pd.Series:
    logret = np.log(close / close.shift(1))
    return logret.rolling(window).std() * np.sqrt(252)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


BUILDERS = {"momentum_20": momentum, "volatility_20": volatility, "rsi_14": rsi}


def build_features(close: pd.Series, symbol: str, run_id: str = None) -> pd.DataFrame:
    """特徴量パネルを作り、生成イベント（元データハッシュ・バージョン）を記録する。"""
    feats = {name: fn(close) for name, fn in BUILDERS.items()}
    df = pd.DataFrame(feats)

    event_log.log_event("feature_generation", {
        "symbol": symbol, "version": VERSION,
        "features": list(BUILDERS.keys()),
        "source_data_hash": _hash_series(close),
        "n_rows": len(df),
        "latest_date": str(df.index[-1].date()) if len(df) else None,
    }, run_id=run_id)

    return df
