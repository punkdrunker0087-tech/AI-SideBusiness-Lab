"""保存レイヤー ―― 生データ・加工済みデータ・メタデータを分けて管理する。

ディレクトリ構成:
  data/raw/{symbol}/{granularity}.csv        取得したそのままのOHLCV
  data/processed/{symbol}/{granularity}.csv  検証・正規化を通過したOHLCV
  data/metadata/{symbol}.json                提供元・取得時刻・更新履歴

ティック/分足/日足のように粒度別にファイルを分けることで、粒度ごとに
異なる保持期間・更新頻度で管理できる（本実装では日足のみ実データ対応）。
"""
import datetime
import json
import os

import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
METADATA_DIR = os.path.join(BASE_DIR, "metadata")


def _ensure_dirs(symbol: str):
    os.makedirs(os.path.join(RAW_DIR, symbol), exist_ok=True)
    os.makedirs(os.path.join(PROCESSED_DIR, symbol), exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)


def save_raw(symbol: str, granularity: str, df: pd.DataFrame) -> str:
    _ensure_dirs(symbol)
    path = os.path.join(RAW_DIR, symbol, f"{granularity}.csv")
    df.to_csv(path)
    return path


def save_processed(symbol: str, granularity: str, df: pd.DataFrame) -> str:
    _ensure_dirs(symbol)
    path = os.path.join(PROCESSED_DIR, symbol, f"{granularity}.csv")
    df.to_csv(path)
    return path


def load_processed(symbol: str, granularity: str) -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, symbol, f"{granularity}.csv")
    return pd.read_csv(path, parse_dates=["date"], index_col="date")


def metadata_path(symbol: str) -> str:
    return os.path.join(METADATA_DIR, f"{symbol}.json")


def load_metadata(symbol: str) -> dict:
    path = metadata_path(symbol)
    if not os.path.exists(path):
        return {"symbol": symbol, "history": []}
    with open(path) as f:
        return json.load(f)


def record_update(symbol: str, source: str, granularity: str, fetched_at: str,
                  n_rows: int, validation_issues: dict, corporate_actions: list = None) -> dict:
    """1回の取得・検証・保存について、メタデータ（更新履歴）に1エントリ追記する。"""
    _ensure_dirs(symbol)
    meta = load_metadata(symbol)
    meta["symbol"] = symbol
    entry = {
        "source": source,
        "granularity": granularity,
        "fetched_at": fetched_at,
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "n_rows": n_rows,
        "had_validation_issues": bool(validation_issues),
        "corporate_actions_detected": corporate_actions or [],
    }
    meta.setdefault("history", []).append(entry)
    meta["last_updated"] = entry["recorded_at"]
    with open(metadata_path(symbol), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    return meta
