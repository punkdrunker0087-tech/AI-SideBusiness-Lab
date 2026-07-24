"""3. リスクパリティ ―― 資産配分でなく「リスクへの寄与」を均等化する。"""
import numpy as np
from scipy.optimize import minimize


def risk_contribution(weights: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """各資産の成分リスク寄与（合計=ポートフォリオボラティリティ）。"""
    port_vol = np.sqrt(weights @ cov @ weights)
    if port_vol == 0:
        return np.zeros_like(weights)
    marginal = cov @ weights
    return weights * marginal / port_vol


def equal_risk_contribution(cov: np.ndarray, max_weight: float = 1.0) -> np.ndarray:
    """各資産のリスク寄与を均等化する重み（Equal Risk Contribution, ERC）。"""
    n = len(cov)

    def objective(w):
        rc = risk_contribution(w, cov)
        target = rc.mean()
        return float(np.sum((rc - target) ** 2))

    res = minimize(
        objective, np.ones(n) / n, method="SLSQP",
        bounds=[(0.0, max_weight)] * n,
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1},
        options={"maxiter": 1000, "ftol": 1e-14},
    )
    return res.x


def diversification_ratio(weights: np.ndarray, cov: np.ndarray) -> float:
    """分散化比率 = 加重平均ボラ / ポートフォリオボラ。高いほど分散が効いている。"""
    asset_vols = np.sqrt(np.diag(cov))
    weighted_avg_vol = weights @ asset_vols
    port_vol = np.sqrt(weights @ cov @ weights)
    return float(weighted_avg_vol / port_vol) if port_vol > 0 else np.nan
