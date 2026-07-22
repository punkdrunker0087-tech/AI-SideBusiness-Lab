"""イベントログ ―― 監査可能性の中核。全判断・処理を時系列で記録する。

データ取得・特徴量生成・モデル推論・仮想約定・エラーを、追記専用の
JSONL（1行1イベント）として保存する。後から「なぜこの日にこの判断が
下されたか」を再構成できることが目的。
"""
import datetime
import json
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "events.jsonl")

EVENT_TYPES = {
    "data_fetch", "data_validation", "feature_generation", "model_inference",
    "paper_fill", "reconciliation", "alert", "error",
}


def log_event(event_type: str, payload: dict, run_id: str = None) -> dict:
    """1イベントを記録する。event_typeはEVENT_TYPESのいずれか。"""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"未知のevent_type: {event_type}（許可: {EVENT_TYPES}）")
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run_id": run_id,
        "event_type": event_type,
        "payload": payload,
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return entry


def read_events(event_type: str = None, run_id: str = None, n: int = None) -> list:
    """ログを読み出す（フィルタ可能）。監査・事後分析の入口。"""
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH) as f:
        events = [json.loads(line) for line in f]
    if event_type:
        events = [e for e in events if e["event_type"] == event_type]
    if run_id:
        events = [e for e in events if e["run_id"] == run_id]
    return events[-n:] if n else events


def clear_log():
    """デモ実行を繰り返す際にログをリセットする（実運用では消さず追記し続ける）。"""
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
