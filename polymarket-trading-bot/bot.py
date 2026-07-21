"""Polymarket 自動売買Bot（実験版）。

デフォルトはドライラン。LIVE_TRADING=true のときのみ実発注する。
実行前に README.md のリスク・免責事項を必ず読むこと。
"""
import json
import logging
import os
import time
from typing import Optional

import requests

import config
import risk
from strategy import simple_momentum_strategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("polymarket-bot")

_PRICE_HISTORY_PATH = os.path.join(os.path.dirname(__file__), "price_history.json")


def _load_price_history() -> dict:
    if not os.path.exists(_PRICE_HISTORY_PATH):
        return {}
    with open(_PRICE_HISTORY_PATH, "r") as f:
        return json.load(f)


def _save_price_history(history: dict) -> None:
    with open(_PRICE_HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)


def fetch_markets() -> list:
    """公開の /markets エンドポイントからアクティブな市場一覧を取得する。"""
    resp = requests.get(f"{config.CLOB_HOST}/markets", timeout=15)
    resp.raise_for_status()
    data = resp.json()
    markets = data.get("data", data) if isinstance(data, dict) else data
    if not isinstance(markets, list):
        log.warning("想定外のレスポンス形式のため市場取得をスキップします")
        return []
    return markets


def _matches_keywords(market: dict) -> bool:
    if not config.MARKET_KEYWORDS:
        return True
    text = " ".join(
        str(market.get(k, "")) for k in ("question", "title", "market_slug")
    ).lower()
    return any(kw.lower() in text for kw in config.MARKET_KEYWORDS)


def _extract_yes_price(market: dict) -> Optional[float]:
    tokens = market.get("tokens") or []
    for token in tokens:
        outcome = str(token.get("outcome", "")).lower()
        if outcome in ("yes", "y"):
            price = token.get("price")
            return float(price) if price is not None else None
    return None


def _place_order(decision) -> None:
    """実発注。py-clob-client 経由でのみ呼び出される想定。

    注文構築(token_id/size等)はPolymarket公式ドキュメントに従って
    利用者自身が検証・調整すること。ここでは安全側に倒し、
    実際の発注コードは意図的にコメントアウトしている。
    """
    order_size_usd = risk.clamp_order_size(config.MAX_ORDER_USD)
    log.warning(
        "LIVE_TRADING=true ですが、安全のため発注コードは無効化されています。"
        " market=%s side=%s price=%.4f size_usd=%.2f reason=%s",
        decision.market_id,
        decision.side,
        decision.price,
        order_size_usd,
        decision.reason,
    )
    # --- 実発注を有効化する場合はここにpy-clob-clientの
    #     create_order / post_order 呼び出しを実装し、
    #     約定結果に応じて risk.record_loss() を呼ぶこと ---


def run_once(history: dict) -> dict:
    if risk.daily_limit_reached():
        log.error(
            "本日の損失上限（%.2f USD）に達しているため、このサイクルはスキップします",
            config.MAX_DAILY_LOSS_USD,
        )
        return history

    markets = fetch_markets()
    log.info("取得した市場数: %d", len(markets))

    for market in markets:
        if not _matches_keywords(market):
            continue

        market_id = str(market.get("condition_id") or market.get("market_slug") or "")
        if not market_id:
            continue

        yes_price = _extract_yes_price(market)
        if yes_price is None:
            continue

        previous_price = history.get(market_id)
        decision = simple_momentum_strategy(market_id, yes_price, previous_price)
        history[market_id] = yes_price

        if decision is None:
            continue

        if config.LIVE_TRADING:
            config.require_live_credentials()
            _place_order(decision)
        else:
            log.info(
                "[DRY RUN] market=%s side=%s price=%.4f reason=%s",
                decision.market_id,
                decision.side,
                decision.price,
                decision.reason,
            )

    return history


def main() -> None:
    mode = "LIVE" if config.LIVE_TRADING else "DRY RUN"
    log.info("Polymarket Bot 起動（モード: %s）", mode)
    if config.LIVE_TRADING:
        log.warning(
            "実資金での発注モードです。README.mdのリスク・免責事項を"
            "理解した上で実行していますか？ 中断するには Ctrl+C"
        )

    history = _load_price_history()
    try:
        while True:
            history = run_once(history)
            _save_price_history(history)
            time.sleep(config.POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        log.info("停止しました")


if __name__ == "__main__":
    main()
