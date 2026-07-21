"""スマート注文ルーティング ―― 複数の流動性供給先を比較し、コストを最小化して配分する。

各執行先(venue)について、利用可能な流動性・レイテンシ・手数料・スプレッドの
違いを考慮し、コストが低い先から優先的に数量を配分する「ウォーターフォール」
方式で配分する。素朴な「流動性シェアに比例配分」と比較することで、
ルーティングの価値を定量化する。
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class Venue:
    name: str
    liquidity_share: float   # その刻みの全体出来高に対するこの先の取扱シェア
    fee_bps: float            # 手数料(bps)
    spread_bps: float         # この先の実効スプレッド(bps)
    latency_ms: float         # 執行レイテンシ(ミリ秒)


def _venue_cost_score(venue: Venue, sigma_step: float, step_duration_ms: float = 300_000) -> float:
    """venue選択の単純なコストスコア（bps換算）。低いほど望ましい。

    レイテンシが長いほど、その間に価格が不利に動くリスク(レイテンシコスト)を
    ボラティリティから概算する: sigma_step・sqrt(latency比率) をbpsに換算。
    """
    latency_ratio = venue.latency_ms / step_duration_ms
    latency_cost_bps = sigma_step * np.sqrt(max(latency_ratio, 0)) * 1e4
    return venue.fee_bps + venue.spread_bps / 2 + latency_cost_bps


def route_naive(qty: float, venues: list) -> dict:
    """素朴な配分: 流動性シェアに比例するだけ（コスト差を考慮しない）。"""
    total_share = sum(v.liquidity_share for v in venues)
    return {v.name: qty * v.liquidity_share / total_share for v in venues}


def route_smart(qty: float, venues: list, step_volume: float,
                sigma_step: float, max_participation: float = 0.3) -> dict:
    """コストの低い先から優先的に配分するウォーターフォール方式。

    各venueには「流動性シェア×その刻みの出来高×参加率上限」で上限を設け、
    安いvenueから順に上限まで詰め、余りを次に安いvenueへ回す。
    """
    scored = sorted(venues, key=lambda v: _venue_cost_score(v, sigma_step))
    remaining = qty
    allocation = {v.name: 0.0 for v in venues}
    for v in scored:
        cap = step_volume * v.liquidity_share * max_participation
        take = min(remaining, cap)
        allocation[v.name] = take
        remaining -= take
        if remaining <= 0:
            break
    if remaining > 0:
        # 全venueの上限を使い切ってもなお残る場合は、最も安い先に積み増す
        allocation[scored[0].name] += remaining
    return allocation


def compare_routing(qty: float, venues: list, step_volume: float,
                    sigma_step: float) -> dict:
    """naive配分とsmart配分の期待コスト（bps）を比較する。"""
    naive = route_naive(qty, venues)
    smart = route_smart(qty, venues, step_volume, sigma_step)

    def _expected_cost_bps(allocation):
        total = sum(allocation.values())
        if total == 0:
            return 0.0
        cost = 0.0
        for v in venues:
            w = allocation[v.name] / total
            cost += w * _venue_cost_score(v, sigma_step)
        return cost

    return {
        "naive_allocation": naive, "smart_allocation": smart,
        "naive_cost_bps": _expected_cost_bps(naive),
        "smart_cost_bps": _expected_cost_bps(smart),
    }
