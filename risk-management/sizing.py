"""2. ポジションサイズ ―― 期待収益でなく「不確実性」で大きさを決める。

実装:
  - inverse_vol      : ボラティリティの逆数で配分（低ボラほど大きく）
  - vol_target       : ポートフォリオを目標年率ボラに合わせてスケール
  - risk_parity      : 各銘柄のリスク寄与を均等化（Equal Risk Contribution）
  - risk_contribution: 各銘柄がポートフォリオ全体リスクに占める寄与
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def ann_cov(returns: pd.DataFrame) -> pd.DataFrame:
    """年率共分散行列。"""
    return returns.cov() * TRADING_DAYS


def inverse_vol(returns: pd.DataFrame) -> pd.Series:
    """逆ボラティリティ配分（合計1）。"""
    vol = returns.std() * np.sqrt(TRADING_DAYS)
    w = 1.0 / vol.replace(0, np.nan)
    return (w / w.sum()).rename("weight")


def portfolio_vol(weights: pd.Series, cov: pd.DataFrame) -> float:
    w = weights.reindex(cov.index).fillna(0.0).values
    return float(np.sqrt(w @ cov.values @ w))


def vol_target(weights: pd.Series, cov: pd.DataFrame, target_vol: float = 0.10) -> pd.Series:
    """目標年率ボラに合わせて全体をスケール（レバレッジ/現金比率が決まる）。"""
    pv = portfolio_vol(weights, cov)
    if pv == 0:
        return weights
    return (weights * (target_vol / pv)).rename("weight")


def risk_contribution(weights: pd.Series, cov: pd.DataFrame) -> pd.DataFrame:
    """各銘柄のリスク寄与（合計=ポートフォリオボラ）と寄与率。"""
    w = weights.reindex(cov.index).fillna(0.0).values
    pv = np.sqrt(w @ cov.values @ w)
    if pv == 0:
        return pd.DataFrame({"risk_contrib": 0.0, "pct": 0.0}, index=cov.index)
    mrc = cov.values @ w                     # 限界リスク寄与
    crc = w * mrc / pv                        # 成分リスク寄与（合計=pv）
    return pd.DataFrame(
        {"weight": w, "risk_contrib": crc, "pct": crc / pv}, index=cov.index
    )


def risk_parity(cov: pd.DataFrame) -> pd.Series:
    """各銘柄のリスク寄与を均等化する long-only 配分（ERC）。"""
    from scipy.optimize import minimize

    n = len(cov)
    C = cov.values

    def obj(w):
        w = np.abs(w)
        w = w / w.sum()
        pv = np.sqrt(w @ C @ w)
        if pv == 0:
            return 1e9
        rc = w * (C @ w) / pv
        return np.sum((rc - rc.mean()) ** 2)   # 寄与の分散を最小化

    res = minimize(
        obj, np.ones(n) / n, method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1},
        options={"maxiter": 500, "ftol": 1e-12},
    )
    w = np.abs(res.x)
    return pd.Series(w / w.sum(), index=cov.index, name="weight")
