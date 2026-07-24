"""在庫管理 ―― 方向性を当てるのではなく、在庫を一方向に偏らせない。

在庫量・在庫の価格感応度・ボラティリティを監視し、必要ならクォートの
非対称化（さらなるスキュー）やヘッジ（外部ヘッジ手段での相殺）を行う。
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class InventoryLimits:
    soft_limit: float = 50.0    # これを超えたらクォートを非対称化して抑制
    hard_limit: float = 100.0   # これを超えたら該当方向のクォートを止める/ヘッジ強制


@dataclass
class InventoryState:
    position: float = 0.0
    cash: float = 0.0
    trade_count: int = 0
    history: list = None

    def __post_init__(self):
        if self.history is None:
            self.history = []

    def record(self, mid: float):
        self.history.append({"position": self.position, "cash": self.cash, "mid": mid})

    def mark_to_market(self, mid: float) -> float:
        """現金＋建玉評価額（NAV相当）。"""
        return self.cash + self.position * mid


def inventory_price_sensitivity(position: float, sigma: float, horizon: float = 1.0) -> float:
    """在庫の価格感応度（ドルデルタ相当）: |position| × σ × sqrt(horizon)。
    在庫量そのものではなく「この在庫がどれだけ動くと危険か」を表す。
    """
    return abs(position) * sigma * np.sqrt(horizon)


def quote_availability(position: float, limits: InventoryLimits) -> dict:
    """現在の在庫水準に基づき、どちら側のクォートを出してよいかを判定する。

    soft_limit超え: 該当方向への追加スキューを推奨（ここでは可否のみ判定し、
                    実際のスキュー強化は quoting.QuoteParams の gamma 調整で行う）
    hard_limit超え: 該当方向のクォート停止（一方通行のみ許可）
    """
    allow_buy = position < limits.hard_limit    # 買い持ちが上限超なら新規買いは停止
    allow_sell = position > -limits.hard_limit  # 売り持ちが上限超なら新規売りは停止
    near_soft = abs(position) > limits.soft_limit
    return {
        "allow_buy_quote": allow_buy,
        "allow_sell_quote": allow_sell,
        "near_soft_limit": near_soft,
        "breach_hard_limit": abs(position) > limits.hard_limit,
    }


def hedge_size(position: float, target: float = 0.0, hedge_ratio: float = 1.0) -> float:
    """在庫をtargetへ近づけるための外部ヘッジ数量（正=買いヘッジ、負=売りヘッジ）。

    hedge_ratio<1.0 は部分ヘッジ（ヘッジコストと在庫リスクのトレードオフ）。
    """
    return -(position - target) * hedge_ratio
