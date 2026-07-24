"""記録保持の基盤 ―― すべてのモジュールが共有する監査ログ。

7節「記録保持」の対象（市場データ・シグナル・リスク判定・注文・約定・
ポジション・モデルバージョン・設定値・システムログ・監査ログ）を、
追記専用のJSONLとして一貫した形式で保存する。
"""
import datetime
import json
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "audit.jsonl")

RECORD_TYPES = {
    "market_data", "signal", "risk_decision", "order", "fill", "position",
    "model_version", "config", "system_log",
    "pretrade_check", "limit_breach", "market_integrity_flag",
    "change_request", "incident", "review", "approval",
}


def record(record_type: str, payload: dict, actor: str = "system") -> dict:
    """1件を記録する。actor=誰が行った/承認したか（職務分掌の追跡に必須）。"""
    if record_type not in RECORD_TYPES:
        raise ValueError(f"未知のrecord_type: {record_type}")
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "record_type": record_type, "actor": actor, "payload": payload,
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return entry


def read(record_type: str = None, actor: str = None, n: int = None) -> list:
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH) as f:
        entries = [json.loads(line) for line in f]
    if record_type:
        entries = [e for e in entries if e["record_type"] == record_type]
    if actor:
        entries = [e for e in entries if e["actor"] == actor]
    return entries[-n:] if n else entries


def clear():
    """デモ再実行のためのリセット（実運用では記録は削除しない）。"""
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
