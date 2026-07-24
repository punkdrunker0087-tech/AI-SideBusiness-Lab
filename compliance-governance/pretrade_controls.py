"""3. 取引前リスクコントロール ―― 注文送信"前"に確認する一連のチェック。

⚠️ これらは判定関数のみであり、実際の注文送信・ブローカー接続は行わない
（このリポジトリ全体の方針と同じ）。「送信して良いか」を判定し、
理由付きで記録することが目的。
"""
import datetime
from dataclasses import dataclass, field

import audit_log


@dataclass
class PreTradeLimits:
    max_order_quantity: float = 10_000
    max_notional: float = 50_000_000.0       # 最大想定約定金額(円)
    max_price_deviation_pct: float = 0.05      # 市場価格からの許容乖離
    price_limit_band_pct: float = 0.10          # 制限値幅の目安
    max_position_quantity: float = 50_000
    max_data_staleness_seconds: int = 60


@dataclass
class OrderRequest:
    symbol: str
    quantity: float          # 正=買い, 負=売り
    limit_price: float
    market_price: float
    current_position: float


@dataclass
class SystemHealth:
    data_is_fresh: bool = True
    data_age_seconds: int = 0
    clock_synced: bool = True
    connection_ok: bool = True


def check_quantity(order: OrderRequest, limits: PreTradeLimits) -> dict:
    ok = abs(order.quantity) <= limits.max_order_quantity
    return {"check": "quantity", "ok": ok,
           "detail": f"数量{abs(order.quantity)} vs 上限{limits.max_order_quantity}"}


def check_notional(order: OrderRequest, limits: PreTradeLimits) -> dict:
    notional = abs(order.quantity) * order.limit_price
    ok = notional <= limits.max_notional
    return {"check": "notional", "ok": ok,
           "detail": f"想定約定金額{notional:,.0f}円 vs 上限{limits.max_notional:,.0f}円"}


def check_price_deviation(order: OrderRequest, limits: PreTradeLimits) -> dict:
    if order.market_price <= 0:
        return {"check": "price_deviation", "ok": False, "detail": "市場価格が不正"}
    deviation = abs(order.limit_price - order.market_price) / order.market_price
    ok = deviation <= limits.max_price_deviation_pct
    return {"check": "price_deviation", "ok": ok,
           "detail": f"乖離{deviation*100:.2f}% vs 上限{limits.max_price_deviation_pct*100:.1f}%"}


def check_position_after_fill(order: OrderRequest, limits: PreTradeLimits) -> dict:
    projected = order.current_position + order.quantity
    ok = abs(projected) <= limits.max_position_quantity
    return {"check": "position_limit", "ok": ok,
           "detail": f"約定後想定保有{projected} vs 上限{limits.max_position_quantity}"}


def check_system_health(health: SystemHealth, limits: PreTradeLimits) -> dict:
    issues = []
    if not health.data_is_fresh or health.data_age_seconds > limits.max_data_staleness_seconds:
        issues.append(f"データ鮮度不良({health.data_age_seconds}秒)")
    if not health.clock_synced:
        issues.append("時刻同期エラー")
    if not health.connection_ok:
        issues.append("接続異常")
    return {"check": "system_health", "ok": not issues, "detail": "; ".join(issues) or "正常"}


def run_all_checks(order: OrderRequest, limits: PreTradeLimits, health: SystemHealth,
                   actor: str = "system") -> dict:
    """全チェックを実行し、1件でもNGなら送信不可(reject)として記録する。"""
    checks = [
        check_quantity(order, limits), check_notional(order, limits),
        check_price_deviation(order, limits), check_position_after_fill(order, limits),
        check_system_health(health, limits),
    ]
    all_ok = all(c["ok"] for c in checks)
    result = {
        "symbol": order.symbol, "quantity": order.quantity, "decision": "承認" if all_ok else "拒否",
        "checks": checks, "failed_checks": [c["check"] for c in checks if not c["ok"]],
    }
    audit_log.record("pretrade_check", result, actor=actor)
    return result
