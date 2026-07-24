"""Paper Trading Layer ―― 仮想約定・仮想損益・仮想コストを管理する。

⚠️ 実際の資金・ブローカーには一切接続しない。研究目的で「もしこの
シグナルで売買していたら」を記録するための仮想会計システム。
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import event_log


@dataclass
class PaperAccount:
    cash: float = 1_000_000.0
    positions: dict = field(default_factory=dict)     # symbol -> 数量
    unit_size: float = 100.0                           # 1シグナルあたりの売買単位
    cost_bps: float = 15.0
    nav_history: list = field(default_factory=list)    # [{"date":..., "nav":...}, ...]
    fills: list = field(default_factory=list)

    def target_position(self, signal: int, confidence: float,
                        min_confidence: float = 0.55) -> float:
        """シグナル・信頼度から目標建玉数量を決める（信頼度が低ければ建玉しない）。"""
        if confidence is None or confidence < min_confidence:
            return 0.0
        return self.unit_size if signal > 0 else 0.0  # 買い/フラットのみ（空売りなし）

    def process_signal(self, symbol: str, signal: int, confidence: float,
                       price: float, date, run_id: str = None) -> dict:
        """シグナルに基づき仮想売買を執行し、仮想約定イベントを記録する。"""
        current = self.positions.get(symbol, 0.0)
        target = self.target_position(signal, confidence)
        trade_qty = target - current

        fill = {"symbol": symbol, "date": str(date.date()), "price": price,
               "trade_qty": trade_qty, "cost": 0.0, "position_after": target}

        if trade_qty != 0:
            cost = abs(trade_qty) * price * (self.cost_bps / 1e4)
            self.cash -= trade_qty * price + cost
            self.positions[symbol] = target
            fill["cost"] = cost

        self.fills.append(fill)
        event_log.log_event("paper_fill", fill, run_id=run_id)
        return fill

    def mark_to_market(self, prices: dict, date) -> float:
        """保有ポジションを時価評価し、NAV履歴に記録する。"""
        position_value = sum(qty * prices.get(sym, 0.0) for sym, qty in self.positions.items())
        nav = self.cash + position_value
        self.nav_history.append({"date": str(date.date()), "nav": nav,
                                 "cash": self.cash, "position_value": position_value})
        return nav

    def exposure_report(self, prices: dict) -> pd.DataFrame:
        rows = []
        for sym, qty in self.positions.items():
            if qty == 0:
                continue
            val = qty * prices.get(sym, 0.0)
            rows.append({"symbol": sym, "qty": qty, "price": prices.get(sym), "value": val})
        return pd.DataFrame(rows)
