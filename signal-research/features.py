"""3. 特徴量設計 ―― 生データを比較可能な形へ変換する。時系列整合性を厳守。

すべての変換は「時点tまでの情報だけ」で計算し、将来情報を含まない。
標準化・ラグ・平滑化・外れ値処理・ランク化を提供する。
"""
import numpy as np
import pandas as pd


# --- 変換プリミティブ ---
def cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """各日、銘柄横断のZスコア（クロスセクション標準化）。"""
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, np.nan), axis=0)


def time_series_zscore(df: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    """各銘柄、過去window日での標準化（時系列標準化）。将来を見ない。"""
    mean = df.rolling(window).mean()
    std = df.rolling(window).std()
    return (df - mean) / std.replace(0, np.nan)


def lag(df: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
    """時間差の導入（過去へずらす＝先読み防止）。"""
    return df.shift(periods)


def smooth(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """移動平均による平滑化。"""
    return df.rolling(window).mean()


def winsorize_cross(df: pd.DataFrame, lower: float = 0.02, upper: float = 0.98) -> pd.DataFrame:
    """各日、銘柄横断で分位クリップ（外れ値の影響を抑える）。"""
    lo = df.quantile(lower, axis=1)
    hi = df.quantile(upper, axis=1)
    return df.clip(lo, hi, axis=0)


def cross_sectional_rank(df: pd.DataFrame) -> pd.DataFrame:
    """各日、銘柄横断のパーセンタイル順位（0〜1）。分布に頑健。"""
    return df.rank(axis=1, pct=True)


# --- ファクター（特徴量）ビルダー ---
def momentum(close: pd.DataFrame, lookback: int = 120) -> pd.DataFrame:
    return close / close.rolling(lookback).mean() - 1


def volatility(close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    logret = np.log(close / close.shift(1))
    return logret.rolling(window).std() * np.sqrt(252)


def liquidity(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    return np.log((close * volume).replace(0, np.nan))


def reversal(close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """直近window日リターン（逆張り仮説では符号が負に効くことを期待）。"""
    return close / close.shift(window) - 1


def build_all(close: pd.DataFrame, volume: pd.DataFrame) -> dict:
    """仮説レジストリに対応する特徴量パネル群を返す（名前→DataFrame）。"""
    return {
        "momentum_120": momentum(close, 120),
        "volatility_20": volatility(close, 20),
        "liquidity_log": liquidity(close, volume),
        "reversal_5": reversal(close, 5),
    }


def forward_return(close: pd.DataFrame, horizon: int = 20) -> pd.DataFrame:
    """時点tから t+horizon の将来リターン（IC評価の被説明変数）。"""
    return close.shift(-horizon) / close - 1
