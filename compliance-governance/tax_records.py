"""11. 税務・会計 ―― 取引記録を税務・会計要件に応じて正確に管理する。

⚠️ 具体的な税務計算方法・必要書類は国・地域・個人の状況によって異なる。
本モジュールは記録の**構造**を示すのみで、税務助言ではない。
実際の申告前には必ず税理士等の専門家に確認すること。
"""
from dataclasses import dataclass

import pandas as pd

import audit_log


@dataclass
class TaxLot:
    symbol: str
    acquisition_date: str
    sale_date: str
    acquisition_price: float
    sale_price: float
    quantity: float
    fees: float = 0.0

    @property
    def holding_period_days(self) -> int:
        acq = pd.Timestamp(self.acquisition_date)
        sale = pd.Timestamp(self.sale_date)
        return (sale - acq).days

    @property
    def realized_pnl(self) -> float:
        return (self.sale_price - self.acquisition_price) * self.quantity - self.fees


def record_lot(lot: TaxLot, actor: str = "back_office") -> dict:
    entry = {
        "symbol": lot.symbol, "acquisition_date": lot.acquisition_date,
        "sale_date": lot.sale_date, "acquisition_price": lot.acquisition_price,
        "sale_price": lot.sale_price, "quantity": lot.quantity, "fees": lot.fees,
        "holding_period_days": lot.holding_period_days, "realized_pnl": lot.realized_pnl,
    }
    audit_log.record("position", {"type": "tax_lot", **entry}, actor=actor)
    return entry


def summarize(lots: list) -> pd.DataFrame:
    """税務用サマリ表（実際の税額計算は行わない。専門家への提出資料の下地）。"""
    rows = [{
        "銘柄": l.symbol, "取得日": l.acquisition_date, "売却日": l.sale_date,
        "保有日数": l.holding_period_days, "実現損益": l.realized_pnl,
        "長期/短期(目安)": "長期" if l.holding_period_days > 365 else "短期",
    } for l in lots]
    return pd.DataFrame(rows)
