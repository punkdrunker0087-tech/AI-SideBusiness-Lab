"""TWAP (Time-Weighted Average Price) ―― 注文を時間的に均等分散する。

適するケース: 流動性が比較的安定・急いで執行する必要がない注文。
出来高の偏りを考慮しないため、出来高が薄い時間帯にも同じ量を執行してしまい
市場インパクトが相対的に大きくなりやすい（VWAPとの比較対象になる所以）。
"""
import numpy as np


def schedule(total_qty: float, n_steps: int) -> np.ndarray:
    """全刻みに均等分散したスケジュールを返す。"""
    return np.full(n_steps, total_qty / n_steps)
