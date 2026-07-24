from dataclasses import dataclass
from typing import Optional


@dataclass
class Decision:
    market_id: str
    side: str  # "BUY_YES" or "BUY_NO"
    price: float
    reason: str


# 収益性は未検証のプレースホルダー戦略。実運用前にバックテストすること。
MOMENTUM_THRESHOLD = 0.05  # 直近価格からの変化率がこれを超えたら追随する


def simple_momentum_strategy(
    market_id: str,
    current_yes_price: float,
    previous_yes_price: Optional[float],
) -> Optional[Decision]:
    """直近のYES価格の変化率がしきい値を超えた方向に追随する単純戦略。

    previous_yes_price が無い(初回観測)場合は判断を保留する。
    """
    if previous_yes_price is None or previous_yes_price <= 0:
        return None

    change_ratio = (current_yes_price - previous_yes_price) / previous_yes_price

    if change_ratio >= MOMENTUM_THRESHOLD:
        return Decision(
            market_id=market_id,
            side="BUY_YES",
            price=current_yes_price,
            reason=f"YES価格が{change_ratio:.1%}上昇したため追随",
        )
    if change_ratio <= -MOMENTUM_THRESHOLD:
        return Decision(
            market_id=market_id,
            side="BUY_NO",
            price=1 - current_yes_price,
            reason=f"YES価格が{change_ratio:.1%}下落したためNO側に追随",
        )
    return None
