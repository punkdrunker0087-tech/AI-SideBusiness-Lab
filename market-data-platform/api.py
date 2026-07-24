"""API・利用インターフェース ―― データ取得方法を統一し、権限・キャッシュ・
監査ログを整備する。

研究・分析コードは個別にファイルパスを触るのでなく、この層を経由することで
「誰が・いつ・何を取得したか」を追跡でき、キャッシュにより重複取得を避ける。
"""
import datetime
import json
import os

import pandas as pd

import storage

AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "audit_log.jsonl")

# 簡易な利用権限（実際にはユーザー/サービスごとのロール管理に発展させる）
_ALLOWED_CALLERS = {"research", "backtest", "monitoring"}


class PermissionError_(Exception):
    pass


def _audit(caller: str, action: str, symbol: str, granularity: str):
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "caller": caller, "action": action, "symbol": symbol, "granularity": granularity,
    }
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


_cache: dict = {}


def get_processed(symbol: str, granularity: str = "1d", caller: str = "research",
                  use_cache: bool = True) -> pd.DataFrame:
    """加工済みデータを取得する（権限チェック・キャッシュ・監査ログ付き）。"""
    if caller not in _ALLOWED_CALLERS:
        raise PermissionError_(f"呼び出し元 '{caller}' は許可リストにありません: {_ALLOWED_CALLERS}")

    key = (symbol, granularity)
    if use_cache and key in _cache:
        _audit(caller, "get_processed(cache_hit)", symbol, granularity)
        return _cache[key]

    df = storage.load_processed(symbol, granularity)
    _cache[key] = df
    _audit(caller, "get_processed(disk_read)", symbol, granularity)
    return df


def read_audit_log(n: int = 20) -> list:
    if not os.path.exists(AUDIT_LOG_PATH):
        return []
    with open(AUDIT_LOG_PATH) as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines[-n:]]
