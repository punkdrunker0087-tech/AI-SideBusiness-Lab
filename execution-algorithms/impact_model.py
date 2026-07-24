"""マーケットインパクト ―― 注文サイズ・流動性・ボラティリティと価格変化の関係。

広く引用される**平方根法則(square-root law)**を採用する:

  temporary_impact = η・σ・sqrt(participation_rate)
  permanent_impact  = γ・σ・participation_rate

  participation_rate = 執行数量 / その時間刻みの市場出来高

一時的インパクト(temporary)は執行直後に解消される価格の歪み、恒久的
インパクト(permanent)は情報効果として仲値に恒久的に残る部分。

参照: Almgren, Thum, Hauptmann, Li (2005) "Direct Estimation of Equity
Market Impact"（平方根法則の実証）
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class ImpactParams:
    eta: float = 0.15    # 一時的インパクト係数
    gamma: float = 0.05  # 恒久的インパクト係数


def participation_rate(order_qty: float, market_volume: float) -> float:
    if market_volume <= 0:
        return 0.0
    return abs(order_qty) / market_volume


def temporary_impact(order_qty: float, market_volume: float, sigma_step: float,
                     params: ImpactParams) -> float:
    """一時的インパクト（相対価格変化率）。執行直後に解消される想定。"""
    pr = participation_rate(order_qty, market_volume)
    return params.eta * sigma_step * np.sqrt(pr) * np.sign(order_qty)


def permanent_impact(order_qty: float, market_volume: float, sigma_step: float,
                     params: ImpactParams) -> float:
    """恒久的インパクト（相対価格変化率）。仲値に恒久的に残る想定。"""
    pr = participation_rate(order_qty, market_volume)
    return params.gamma * sigma_step * pr * np.sign(order_qty)
