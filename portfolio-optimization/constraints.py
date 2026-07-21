"""制約条件 ―― 最適化だけでなく、現実的な運用制約を課す。

個別資産集中・グループ(資産クラス)偏り・回転率・レバレッジを扱う。
"""
import numpy as np


def apply_position_limit(weights: np.ndarray, max_weight: float) -> np.ndarray:
    """個別資産への集中を抑え、超過分を他資産へ比例配分し直す。"""
    w = np.clip(weights, 0, max_weight)
    total = w.sum()
    return w / total if total > 0 else w


def apply_group_limit(weights: np.ndarray, groups: list, max_group_weight: float) -> np.ndarray:
    """グループ（例: 資産クラス・地域）への偏りを抑える。

    groups: 各資産が属するグループ名のリスト（weightsと同じ長さ）。
    グループ合計が上限を超えたら、そのグループ内で比例縮小し、
    浮いた分を他グループへ比例配分する。
    """
    w = weights.copy()
    groups = np.array(groups)
    for g in np.unique(groups):
        mask = groups == g
        group_sum = w[mask].sum()
        if group_sum > max_group_weight and group_sum > 0:
            w[mask] *= max_group_weight / group_sum
    total = w.sum()
    return w / total if total > 0 else w


def apply_turnover_limit(target_weights: np.ndarray, current_weights: np.ndarray,
                        max_turnover: float) -> np.ndarray:
    """理想配分(target)へ一気に動かず、回転率上限の範囲でしか動かさない。

    turnover = sum(|target - current|) を上限内に収める（比例縮小）。
    """
    delta = target_weights - current_weights
    turnover = np.abs(delta).sum()
    if turnover <= max_turnover or turnover == 0:
        return target_weights
    scale = max_turnover / turnover
    return current_weights + delta * scale


def apply_leverage_limit(weights: np.ndarray, max_gross: float = 1.0) -> np.ndarray:
    """総エクスポージャー（グロス）の上限。long-onlyならsum(weights)=grossなので単純比例縮小。"""
    gross = np.abs(weights).sum()
    if gross <= max_gross or gross == 0:
        return weights
    return weights * (max_gross / gross)
