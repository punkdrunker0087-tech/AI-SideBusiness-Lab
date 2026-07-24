"""スプレッドの分析 ―― 価格差そのものでなく、関係性から導かれる残差を扱う。

spread[t] = y[t] − hedge_ratio・x[t]

長期平均・分散・安定性（ローリング統計の推移）・自己相関を評価し、
平均回帰の速度（半減期）をOrnstein-Uhlenbeck過程の離散近似で推定する。
"""
import numpy as np
import pandas as pd


def build_spread(y: pd.Series, x: pd.Series, hedge_ratio: float, alpha: float = 0.0) -> pd.Series:
    """コインテグレーション回帰から得たヘッジ比率でスプレッドを構築する。"""
    df = pd.concat([y, x], axis=1).dropna()
    return (df.iloc[:, 0] - alpha - hedge_ratio * df.iloc[:, 1]).rename("spread")


def spread_stats(spread: pd.Series) -> dict:
    """長期平均・分散・自己相関（1次）を返す。"""
    s = spread.dropna()
    return {
        "mean": float(s.mean()),
        "std": float(s.std()),
        "autocorr_1": float(s.autocorr(1)),
        "n": len(s),
    }


def rolling_stability(spread: pd.Series, window: int = 60) -> pd.DataFrame:
    """ローリング平均・標準偏差の推移（スプレッドの安定性を目視で確認する用）。"""
    return pd.DataFrame({
        "rolling_mean": spread.rolling(window).mean(),
        "rolling_std": spread.rolling(window).std(),
    })


def half_life(spread: pd.Series) -> dict:
    """平均回帰速度（半減期）をOU過程の離散化(AR(1))から推定する。

    Δspread[t] = θ・(μ − spread[t-1]) + ε[t]  を回帰すると、
    θ が平均回帰速度。半減期 = ln(2) / θ （日数）。
    θ ≤ 0（トレンドに乗る／回帰しない）なら half_life = inf として扱う。
    """
    s = spread.dropna()
    lagged = s.shift(1)
    delta = s - lagged
    df = pd.concat([delta, lagged], axis=1).dropna()
    df.columns = ["delta", "lagged"]
    if len(df) < 30:
        return {"theta": np.nan, "half_life_days": np.nan, "mu": np.nan}

    X = np.column_stack([np.ones(len(df)), df["lagged"].values])
    beta, *_ = np.linalg.lstsq(X, df["delta"].values, rcond=None)
    c, b = beta                       # delta = c + b・lagged  →  θ = −b, μ = −c/b
    theta = -b
    mu = -c / b if b != 0 else np.nan

    if theta <= 0:
        hl = np.inf
    else:
        hl = np.log(2) / theta
    return {"theta": float(theta), "half_life_days": float(hl), "mu": float(mu)}
