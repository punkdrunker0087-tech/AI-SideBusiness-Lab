"""5. 市場公正性 ―― 自己約定・不自然な注文取消・相場操縦の兆候を検知する。

検知結果は自動的にブロックするのではなく、**人によるレビュー対象として
フラグを立てる**（誤検知のリスクがあるため、最終判断は人が行う）。
"""
from collections import Counter
from dataclasses import dataclass

import audit_log


@dataclass
class OrderEvent:
    order_id: str
    account: str
    symbol: str
    side: str          # "buy" / "sell"
    quantity: float
    price: float
    status: str          # "new" / "cancel" / "fill"
    ts: str


def detect_self_trades(fills: list) -> list:
    """同一アカウントの買い約定と売り約定が同時刻・同銘柄・同価格帯で
    対向していないか（自己約定の疑い）を検知する。
    """
    flags = []
    by_key = {}
    for f in fills:
        key = (f["account"], f["symbol"], f["ts"])
        by_key.setdefault(key, []).append(f)

    for key, group in by_key.items():
        sides = {g["side"] for g in group}
        if "buy" in sides and "sell" in sides:
            flags.append({"type": "self_trade_suspect", "account": key[0], "symbol": key[1],
                         "ts": key[2], "detail": "同一口座・同時刻に買いと売りが対向"})
    return flags


def detect_excessive_cancel_ratio(orders: list, threshold: float = 0.90, min_orders: int = 20) -> list:
    """注文のキャンセル率が異常に高いアカウントを検知する（クオートスタッフィング等の兆候）。"""
    flags = []
    by_account = {}
    for o in orders:
        by_account.setdefault(o["account"], []).append(o)

    for account, group in by_account.items():
        if len(group) < min_orders:
            continue
        n_cancel = sum(1 for o in group if o["status"] == "cancel")
        ratio = n_cancel / len(group)
        if ratio >= threshold:
            flags.append({"type": "excessive_cancel_ratio", "account": account,
                         "cancel_ratio": ratio, "n_orders": len(group),
                         "detail": f"キャンセル率{ratio*100:.0f}%（{len(group)}件中）"})
    return flags


def detect_marking_the_close(orders: list, close_window_minutes: int = 5) -> list:
    """引け間際の一方向への集中発注（相場を誤認させる行為の兆候）を検知する。

    close_window内の注文が、その口座の当日全注文に対して偏った方向に
    集中している場合にフラグを立てる（簡易ヒューリスティック）。
    """
    from datetime import datetime, timedelta

    flags = []
    by_account = {}
    for o in orders:
        by_account.setdefault(o["account"], []).append(o)

    for account, group in by_account.items():
        if not group:
            continue
        times = [datetime.fromisoformat(o["ts"]) for o in group]
        day_end = max(times)
        window_start = day_end - timedelta(minutes=close_window_minutes)
        late_orders = [o for o, t in zip(group, times) if t >= window_start]
        if len(late_orders) < 5:
            continue
        side_counts = Counter(o["side"] for o in late_orders)
        dominant_side, dominant_n = side_counts.most_common(1)[0]
        concentration = dominant_n / len(late_orders)
        if concentration >= 0.9 and len(late_orders) >= 0.5 * len(group):
            flags.append({"type": "marking_the_close_suspect", "account": account,
                         "detail": f"引け前{close_window_minutes}分に{dominant_side}が"
                                  f"{concentration*100:.0f}%集中（{len(late_orders)}件）"})
    return flags


def run_surveillance(orders: list, fills: list, actor: str = "compliance_surveillance") -> dict:
    """全検知ロジックを実行し、フラグをエスカレーション対象として記録する。"""
    flags = (detect_self_trades(fills) + detect_excessive_cancel_ratio(orders)
            + detect_marking_the_close(orders))
    for f in flags:
        audit_log.record("market_integrity_flag", f, actor=actor)
    return {"n_flags": len(flags), "flags": flags,
           "requires_human_review": len(flags) > 0}
