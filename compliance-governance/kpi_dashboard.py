"""12. KPI ―― システム・リスク・コンプライアンス・データ品質・変更管理・
インシデントの各分類で運用状況を継続的に把握する。
"""
import numpy as np
import pandas as pd

import audit_log


def compute_kpis() -> dict:
    """監査ログ全体からKPIを集計する。"""
    all_entries = audit_log.read()
    by_type = {}
    for e in all_entries:
        by_type.setdefault(e["record_type"], []).append(e)

    pretrade = by_type.get("pretrade_check", [])
    n_rejected = sum(1 for e in pretrade if e["payload"].get("decision") == "拒否")

    breaches = by_type.get("limit_breach", [])
    n_hard = sum(1 for e in breaches if e["payload"].get("limit_type") == "hard")
    n_soft = sum(1 for e in breaches if e["payload"].get("limit_type") == "soft")

    flags = by_type.get("market_integrity_flag", [])

    changes = by_type.get("change_request", [])
    n_rollback = sum(1 for e in changes if e["payload"].get("state") == "rolled_back")
    n_deployed = sum(1 for e in changes if e["payload"].get("state") == "deployed")

    incidents = by_type.get("incident", [])
    incident_ids = {e["payload"]["incident_id"] for e in incidents}

    return {
        "システム": {"監査ログ総イベント数": len(all_entries)},
        "リスク": {"リミット超過(ハード)": n_hard, "リミット超過(ソフト)": n_soft,
                 "取引前チェック拒否件数": n_rejected},
        "コンプライアンス": {"市場公正性フラグ件数": len(flags)},
        "変更管理": {"デプロイ件数": n_deployed, "ロールバック件数": n_rollback,
                  "ロールバック率": (n_rollback / n_deployed) if n_deployed else np.nan},
        "インシデント": {"インシデント件数": len(incident_ids)},
    }


def format_dashboard(kpis: dict) -> str:
    lines = ["=== KPIダッシュボード ==="]
    for category, metrics in kpis.items():
        lines.append(f"\n[{category}]")
        for k, v in metrics.items():
            if isinstance(v, float) and not np.isnan(v):
                lines.append(f"  {k}: {v:.2%}" if "率" in k else f"  {k}: {v:.2f}")
            else:
                lines.append(f"  {k}: {v}")
    return "\n".join(lines)
