import datetime
import json
import os

import config

_LEDGER_PATH = os.path.join(os.path.dirname(__file__), "daily_pnl.json")


def _today() -> str:
    return datetime.date.today().isoformat()


def _load_ledger() -> dict:
    if not os.path.exists(_LEDGER_PATH):
        return {}
    with open(_LEDGER_PATH, "r") as f:
        return json.load(f)


def _save_ledger(ledger: dict) -> None:
    with open(_LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=2)


def record_loss(amount_usd: float) -> None:
    """amount_usd: 損失なら正の値で記録する（利益は記録しない = 保守的）"""
    ledger = _load_ledger()
    day = _today()
    ledger[day] = ledger.get(day, 0.0) + amount_usd
    _save_ledger(ledger)


def daily_loss_so_far() -> float:
    ledger = _load_ledger()
    return ledger.get(_today(), 0.0)


def daily_limit_reached() -> bool:
    return daily_loss_so_far() >= config.MAX_DAILY_LOSS_USD


def clamp_order_size(desired_usd: float) -> float:
    """1注文あたりの上限額でクランプする"""
    return min(desired_usd, config.MAX_ORDER_USD)
