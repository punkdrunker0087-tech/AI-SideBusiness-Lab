"""10. レビュー計画 ―― 毎日/毎週/毎月/四半期/年次のレビューサイクルを追跡する。"""
import datetime
from dataclasses import dataclass, field

import audit_log

SCHEDULE = {
    "daily": {"interval_days": 1, "content": "リスク・例外・ログ確認"},
    "weekly": {"interval_days": 7, "content": "データ品質・運用状況レビュー"},
    "monthly": {"interval_days": 30, "content": "コンプライアンス指標・変更管理レビュー"},
    "quarterly": {"interval_days": 91, "content": "リスク評価・手順の見直し"},
    "annual": {"interval_days": 365, "content": "ガバナンス全体・監査対応・教育"},
}


def complete_review(cadence: str, findings: str, actor: str) -> dict:
    if cadence not in SCHEDULE:
        raise ValueError(f"未定義のレビュー周期: {cadence}")
    entry = {"cadence": cadence, "content": SCHEDULE[cadence]["content"],
            "findings": findings, "completed_at": datetime.date.today().isoformat()}
    audit_log.record("review", entry, actor=actor)
    return entry


def next_due_report(last_completed: dict) -> list:
    """各周期の最終実施日から、次回期限と現在の遅延状況を計算する。

    last_completed: {"daily": "2026-07-20", "weekly": "2026-07-14", ...}
    """
    today = datetime.date.today()
    rows = []
    for cadence, spec in SCHEDULE.items():
        last_str = last_completed.get(cadence)
        if last_str is None:
            rows.append({"周期": cadence, "内容": spec["content"], "状態": "未実施"})
            continue
        last_date = datetime.date.fromisoformat(last_str)
        due = last_date + datetime.timedelta(days=spec["interval_days"])
        overdue_days = (today - due).days
        status = f"期限超過({overdue_days}日)" if overdue_days > 0 else "○ 期限内"
        rows.append({"周期": cadence, "内容": spec["content"], "前回実施": last_str,
                    "次回期限": due.isoformat(), "状態": status})
    return rows
