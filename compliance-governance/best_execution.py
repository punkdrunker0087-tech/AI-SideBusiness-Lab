"""6. 最良執行 ―― 注文時刻・市場状況・執行価格・執行場所・手数料・スリッページを
記録し、執行品質を継続的に評価する（コンプライアンス記録としての側面）。

執行品質の詳細な分析自体は `../execution-algorithms/tca.py` を参照。
ここでは**コンプライアンス上の記録要件**としての最小構造を扱う。
"""
from dataclasses import dataclass

import pandas as pd

import audit_log


@dataclass
class ExecutionRecord:
    order_time: str
    symbol: str
    venue: str
    execution_price: float
    reference_price: float   # 発注時点の市場価格（スリッページ算出用）
    commission_bps: float


def slippage_bps(record: ExecutionRecord) -> float:
    if record.reference_price <= 0:
        return float("nan")
    return (record.execution_price / record.reference_price - 1) * 1e4


def record_execution(record: ExecutionRecord, actor: str = "execution_desk") -> dict:
    entry = {
        "order_time": record.order_time, "symbol": record.symbol, "venue": record.venue,
        "execution_price": record.execution_price, "reference_price": record.reference_price,
        "slippage_bps": slippage_bps(record), "commission_bps": record.commission_bps,
    }
    audit_log.record("fill", entry, actor=actor)
    return entry


def quality_summary(records: list) -> pd.DataFrame:
    df = pd.DataFrame([{
        "銘柄": r.symbol, "執行場所": r.venue, "スリッページ(bps)": slippage_bps(r),
        "手数料(bps)": r.commission_bps,
    } for r in records])
    if df.empty:
        return df
    return df.groupby("執行場所").agg({"スリッページ(bps)": "mean", "手数料(bps)": "mean"}).round(2)
