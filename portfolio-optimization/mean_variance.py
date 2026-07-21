"""1. 平均分散最適化 ―― 期待リターンと共分散のバランス（Markowitz 1952）。

期待リターン・共分散の**推定誤差に結果が敏感**という古典的な問題を、
ブートストラップで定量的に確認する機能もあわせて提供する。
"""
import numpy as np
from scipy.optimize import minimize

TRADING_DAYS = 252


def expected_returns(returns) -> np.ndarray:
    return returns.mean().values * TRADING_DAYS


def covariance(returns) -> np.ndarray:
    return returns.cov().values * TRADING_DAYS


def _bounds(n, max_weight=1.0):
    return [(0.0, max_weight)] * n


def min_variance_weights(cov: np.ndarray, max_weight: float = 1.0) -> np.ndarray:
    n = len(cov)
    res = minimize(
        lambda w: w @ cov @ w, np.ones(n) / n, method="SLSQP",
        bounds=_bounds(n, max_weight),
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1},
        options={"maxiter": 500, "ftol": 1e-12},
    )
    return res.x


def max_sharpe_weights(mu: np.ndarray, cov: np.ndarray, rf: float = 0.0,
                       max_weight: float = 1.0) -> np.ndarray:
    n = len(mu)

    def neg_sharpe(w):
        ret = w @ mu
        vol = np.sqrt(w @ cov @ w)
        return -(ret - rf) / vol if vol > 0 else 1e9

    res = minimize(
        neg_sharpe, np.ones(n) / n, method="SLSQP",
        bounds=_bounds(n, max_weight),
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1},
        options={"maxiter": 500, "ftol": 1e-12},
    )
    return res.x


def target_return_weights(mu: np.ndarray, cov: np.ndarray, target: float,
                          max_weight: float = 1.0) -> np.ndarray:
    """目標リターンを達成する最小分散ポートフォリオ（効率的フロンティア上の1点）。"""
    n = len(mu)
    res = minimize(
        lambda w: w @ cov @ w, np.ones(n) / n, method="SLSQP",
        bounds=_bounds(n, max_weight),
        constraints=[
            {"type": "eq", "fun": lambda w: w.sum() - 1},
            {"type": "eq", "fun": lambda w: w @ mu - target},
        ],
        options={"maxiter": 500, "ftol": 1e-12},
    )
    return res.x if res.success else None


def efficient_frontier(mu: np.ndarray, cov: np.ndarray, n_points: int = 20,
                       max_weight: float = 1.0) -> list:
    """効率的フロンティア上の点群 [(リターン, ボラ, 重み), ...] を返す。"""
    targets = np.linspace(mu.min(), mu.max(), n_points)
    points = []
    for t in targets:
        w = target_return_weights(mu, cov, t, max_weight)
        if w is None:
            continue
        vol = float(np.sqrt(w @ cov @ w))
        points.append((float(t), vol, w))
    return points


def bootstrap_weight_stability(returns, n_boot: int = 200, block_size: int = 20,
                              max_weight: float = 1.0, seed: int = 0) -> dict:
    """推定誤差への感応度: リターンをブロック・ブートストラップし、
    その都度 max_sharpe_weights を再計算して重みの安定性（標準偏差）を測る。
    """
    rng = np.random.default_rng(seed)
    n_days, n_assets = returns.shape
    all_weights = []

    for _ in range(n_boot):
        n_blocks = n_days // block_size
        idx = []
        for _ in range(n_blocks):
            start = rng.integers(0, n_days - block_size)
            idx.extend(range(start, start + block_size))
        sample = returns.iloc[idx]
        mu = expected_returns(sample)
        cov = covariance(sample)
        w = max_sharpe_weights(mu, cov, max_weight=max_weight)
        all_weights.append(w)

    W = np.array(all_weights)
    return {
        "mean_weights": W.mean(axis=0),
        "std_weights": W.std(axis=0),
        "min_weights": W.min(axis=0),
        "max_weights": W.max(axis=0),
        "n_boot": n_boot,
    }
