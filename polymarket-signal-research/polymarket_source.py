"""Polymarket の公開データを *読み取り専用* で取得するモジュール。

ここでは一切「賭け」を行わない。ウォレット接続もAPIキーも使わず、
誰でも見られる公開エンドポイントから、市場の確率(価格)の時系列を取得する。
用途は、Polymarketの確率が他の合法的な金融商品の値動きに対して
予測力を持つかを検証する「シグナル研究」である。

エンドポイント:
- 市場一覧:   https://gamma-api.polymarket.com/markets
- 価格履歴:   https://clob.polymarket.com/prices-history
"""
import json
from dataclasses import dataclass

import requests

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"


@dataclass
class Market:
    question: str
    condition_id: str
    yes_token_id: str
    no_token_id: str
    volume_usd: float
    end_date: str


def search_markets(keyword: str = "", limit: int = 200) -> list:
    """出来高順にアクティブな市場を取得し、キーワードで絞り込む。"""
    resp = requests.get(
        f"{GAMMA}/markets",
        params={
            "closed": "false",
            "limit": limit,
            "order": "volumeNum",
            "ascending": "false",
        },
        timeout=25,
    )
    resp.raise_for_status()
    markets = []
    for m in resp.json():
        question = m.get("question") or ""
        if keyword and keyword.lower() not in question.lower():
            continue
        token_ids = m.get("clobTokenIds")
        if isinstance(token_ids, str):
            try:
                token_ids = json.loads(token_ids)
            except json.JSONDecodeError:
                token_ids = []
        if not token_ids or len(token_ids) < 2:
            continue
        markets.append(
            Market(
                question=question,
                condition_id=m.get("conditionId", ""),
                yes_token_id=str(token_ids[0]),
                no_token_id=str(token_ids[1]),
                volume_usd=float(m.get("volumeNum") or 0.0),
                end_date=m.get("endDate", ""),
            )
        )
    return markets


def search_events(query: str, limit: int = 10) -> list:
    """gammaの全文検索。価格連動市場(例: 'Bitcoin above')の発掘に使う。

    戻り値: Market のリスト(イベント内の各ストライクを1市場として展開)。
    """
    resp = requests.get(
        f"{GAMMA}/public-search",
        params={"q": query, "limit_per_type": limit},
        timeout=25,
    )
    resp.raise_for_status()
    events = resp.json().get("events", [])
    markets = []
    for e in events:
        for m in e.get("markets", []):
            token_ids = m.get("clobTokenIds")
            if isinstance(token_ids, str):
                try:
                    token_ids = json.loads(token_ids)
                except json.JSONDecodeError:
                    continue
            if not token_ids or len(token_ids) < 2:
                continue
            markets.append(
                Market(
                    question=m.get("question") or e.get("title", ""),
                    condition_id=m.get("conditionId", ""),
                    yes_token_id=str(token_ids[0]),
                    no_token_id=str(token_ids[1]),
                    volume_usd=float(m.get("volumeNum") or 0.0),
                    end_date=m.get("endDate", ""),
                )
            )
    return markets


def price_history(token_id: str, interval: str = "1m", fidelity: int = 60) -> list:
    """指定トークン(YES/NO)の価格(=確率)時系列を取得する。

    戻り値: [{"t": unix_seconds, "p": price_0_to_1}, ...]
    interval: "1m"(1ヶ月) / "1w" / "1d" / "max" など
    fidelity: サンプリング間隔(分)。60 = 1時間ごと
    """
    resp = requests.get(
        f"{CLOB}/prices-history",
        params={"market": token_id, "interval": interval, "fidelity": fidelity},
        timeout=25,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("history", data if isinstance(data, list) else [])
