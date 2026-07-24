"""クォート生成 ―― Avellaneda-Stoikov (2008) の在庫リスク・クォートモデル。

マーケットメイカーは仲値(mid)そのものではなく、**在庫を考慮した留保価格
(reservation price)** を中心にビッド/アスクを出す。在庫が多いほど売りたいので
留保価格を下げ、在庫が少ない（または売り持ち）ほど買いたいので上げる。
これが「価格の方向を当てる」のではなく「在庫を中立に保つ」設計思想の核心。

reservation_price = mid − inventory・γ・σ²・(T−t)
optimal_spread    = γ・σ²・(T−t) + (2/γ)・ln(1 + γ/κ)

  γ (gamma) : リスク回避度。大きいほど在庫を嫌い、スキューを強くかける
  σ (sigma) : ボラティリティ
  κ (kappa) : 注文到着強度の価格感応度（板の厚さ・逆選択の代理）
  T−t       : 残り時間（セッション終了が近いほど在庫を早く畳みたくなる）

参照: Avellaneda, M. & Stoikov, S. (2008)
"High-frequency trading in a limit order book"
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class QuoteParams:
    gamma: float = 0.1       # リスク回避度
    kappa: float = 1.5       # 注文到着強度の価格感応度
    sigma: float = 2.0       # ボラティリティ（価格と同じ単位の1秒あたり標準偏差 等）


@dataclass
class Quote:
    bid: float
    ask: float
    reservation_price: float
    half_spread: float


def reservation_price(mid: float, inventory: float, params: QuoteParams,
                      time_remaining: float) -> float:
    """在庫を考慮した留保価格。inventory>0(買い持ち)ほど価格を下げ、売りたくなる。"""
    return mid - inventory * params.gamma * params.sigma ** 2 * time_remaining


def optimal_half_spread(params: QuoteParams, time_remaining: float) -> float:
    """最適スプレッドの半分。ボラ・残り時間が大きいほど、板が薄い(κ小)ほど広がる。"""
    inventory_term = params.gamma * params.sigma ** 2 * time_remaining
    liquidity_term = (2.0 / params.gamma) * np.log(1 + params.gamma / params.kappa)
    return (inventory_term + liquidity_term) / 2.0


def make_quotes(mid: float, inventory: float, params: QuoteParams,
                time_remaining: float, min_spread: float = 0.0) -> Quote:
    """ビッド/アスクの実際のクォートを生成する。"""
    r = reservation_price(mid, inventory, params, time_remaining)
    hs = max(optimal_half_spread(params, time_remaining), min_spread / 2.0)
    return Quote(bid=r - hs, ask=r + hs, reservation_price=r, half_spread=hs)
