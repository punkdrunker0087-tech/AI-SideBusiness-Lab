"""リコンシリエーション ―― 入力データ・モデル出力・仮想ポジションの整合性確認。

研究環境でも、ログに残された記録と現在の状態を突き合わせることで、
データ不整合やロジックの問題（バグ）を早期に発見する。実際にこの
リポジトリの複数のフレームワークで、同じような照合を通じてバグを
発見してきた（例: リバランス日付選定バグ・Embargoロジックのバグ）。
"""
import numpy as np
import pandas as pd

import event_log


def reconcile_positions(account, run_id: str = None) -> dict:
    """PaperAccount.positions（現在の内部状態）と、イベントログの約定履歴から
    再計算したポジション（cumulative sum of trade_qty）を突き合わせる。
    """
    fills = event_log.read_events("paper_fill", run_id=run_id)
    recomputed = {}
    for f in fills:
        p = f["payload"]
        recomputed[p["symbol"]] = recomputed.get(p["symbol"], 0.0) + p["trade_qty"]

    mismatches = []
    all_symbols = set(account.positions) | set(recomputed)
    for sym in all_symbols:
        live = account.positions.get(sym, 0.0)
        logged = recomputed.get(sym, 0.0)
        if abs(live - logged) > 1e-6:
            mismatches.append({"symbol": sym, "live_position": live, "log_derived_position": logged,
                              "diff": live - logged})

    return {
        "n_symbols_checked": len(all_symbols),
        "n_mismatches": len(mismatches),
        "mismatches": mismatches,
        "verdict": "○ 内部状態とログが一致" if not mismatches else "⚠️ 不一致検出（要調査）",
    }


def reconcile_model_decisions(account, run_id: str = None, min_confidence: float = 0.55) -> dict:
    """モデル推論ログと約定ログを突き合わせ、
    「シグナル・信頼度から期待される建玉」と「実際の約定」が整合するかを確認する。
    """
    inferences = {(e["payload"]["symbol"], e["payload"]["date"]): e["payload"]
                 for e in event_log.read_events("model_inference", run_id=run_id)}
    fills = event_log.read_events("paper_fill", run_id=run_id)

    mismatches = []
    for f in fills:
        p = f["payload"]
        key = (p["symbol"], p["date"])
        inf = inferences.get(key)
        if inf is None:
            mismatches.append({"symbol": p["symbol"], "date": p["date"],
                              "issue": "対応する推論ログが見つからない"})
            continue
        expected_target = account.target_position(inf["signal"], inf.get("confidence"), min_confidence)
        if abs(expected_target - p["position_after"]) > 1e-6:
            mismatches.append({"symbol": p["symbol"], "date": p["date"],
                              "expected": expected_target, "actual": p["position_after"]})

    return {
        "n_fills_checked": len(fills),
        "n_mismatches": len(mismatches),
        "mismatches": mismatches,
        "verdict": "○ モデル判断と約定が整合" if not mismatches else "⚠️ 不一致検出（要調査）",
    }


def full_reconciliation(account, run_id: str = None) -> dict:
    pos = reconcile_positions(account, run_id)
    dec = reconcile_model_decisions(account, run_id)
    event_log.log_event("reconciliation", {
        "position_check": pos["verdict"], "decision_check": dec["verdict"],
        "n_position_mismatches": pos["n_mismatches"], "n_decision_mismatches": dec["n_mismatches"],
    }, run_id=run_id)
    return {"positions": pos, "decisions": dec}
