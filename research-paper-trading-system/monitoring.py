"""Monitoring Dashboard ―― データ遅延・モデルドリフト・仮想損益・推論時間・稼働状況。

イベントログとPaperAccountの状態から、監視項目を1枚のダッシュボードに集約する。
"""
import time

import numpy as np
import pandas as pd

import event_log
import model_layer


def data_delay_report(run_id: str = None) -> pd.DataFrame:
    events = event_log.read_events("data_validation", run_id=run_id)
    rows = [{"symbol": e["payload"]["symbol"], "latency_days": e["payload"]["latency_days"],
            "ts": e["ts"]} for e in events]
    return pd.DataFrame(rows)


def model_drift_report(run_id: str = None, baseline_n: int = 60, window_n: int = 40) -> dict:
    """モデルドリフトを銘柄別に評価する。

    プールして比較すると「銘柄ごとの確信度分布の違い」がドリフトと誤認される
    ため、必ず銘柄ごとに分けて計算する。また比較対象を毎回動く前半/後半に
    すると基準がぶれて安定しないため、**各銘柄の最初のbaseline_n件**を
    固定ベースラインとし、それ以降の**直近window_n件**を「現在の分布」として
    比較する（実装時、プール＋動く分割で全日アラートが発火する過検知を
    実際に起こして発見・修正した）。
    """
    events = event_log.read_events("model_inference", run_id=run_id)
    by_symbol = {}
    for e in events:
        p = e["payload"]
        if p.get("confidence") is None:
            continue
        by_symbol.setdefault(p["symbol"], []).append(p["confidence"])

    per_symbol = {}
    for sym, confs in by_symbol.items():
        arr = np.array(confs)
        if len(arr) < baseline_n + window_n:
            per_symbol[sym] = {"psi": np.nan, "n": len(arr)}
            continue
        baseline = arr[:baseline_n]
        current = arr[-window_n:]
        psi = model_layer.population_stability_index(baseline, current)
        per_symbol[sym] = {"psi": psi, "n": len(arr)}

    valid_psi = [v["psi"] for v in per_symbol.values() if not np.isnan(v["psi"])]
    if not valid_psi:
        return {"psi": np.nan, "verdict": "判定不能（データ不足）", "per_symbol": per_symbol}

    worst_psi = max(valid_psi)
    verdict = "○安定" if worst_psi < 0.1 else "△要注意" if worst_psi < 0.25 else "⚠️大きく変化"
    return {"psi": worst_psi, "verdict": verdict, "per_symbol": per_symbol,
           "n_inferences": sum(len(c) for c in by_symbol.values())}


def virtual_pnl_report(account) -> dict:
    if not account.nav_history:
        return {}
    nav = pd.DataFrame(account.nav_history)
    total_return = nav["nav"].iloc[-1] / nav["nav"].iloc[0] - 1
    dd = (nav["nav"] / nav["nav"].cummax() - 1).min()
    return {
        "starting_nav": float(nav["nav"].iloc[0]), "current_nav": float(nav["nav"].iloc[-1]),
        "total_return": float(total_return), "max_drawdown": float(dd),
        "n_fills": len(account.fills), "total_cost": float(sum(f["cost"] for f in account.fills)),
    }


def inference_latency_check(model, features_row: pd.Series) -> float:
    """1回の推論にかかった時間（ミリ秒）を計測する（システム健全性の監視項目）。"""
    t0 = time.perf_counter()
    if not features_row.isna().any():
        model.predict_proba(features_row.to_frame().T)
    return (time.perf_counter() - t0) * 1000


def system_uptime_report(run_id: str = None) -> dict:
    errors = event_log.read_events("error", run_id=run_id)
    all_events = event_log.read_events(run_id=run_id)
    return {
        "n_events": len(all_events), "n_errors": len(errors),
        "error_rate": len(errors) / len(all_events) if all_events else np.nan,
        "verdict": "○ 正常" if len(errors) == 0 else f"⚠️ エラー{len(errors)}件検出",
    }


def dashboard(account, run_id: str = None) -> str:
    """全監視項目を1枚のテキストダッシュボードにまとめる。"""
    lines = ["=== Monitoring Dashboard ==="]

    delay = data_delay_report(run_id)
    if not delay.empty:
        lines.append(f"データ遅延: 最新{delay['latency_days'].max()}日 "
                     f"(監視銘柄{delay['symbol'].nunique()}件)")

    drift = model_drift_report(run_id)
    lines.append(f"モデルドリフト(推論信頼度PSI): {drift.get('psi', float('nan')):.3f}  "
                f"{drift.get('verdict', '')}" if not np.isnan(drift.get("psi", np.nan))
                else f"モデルドリフト: {drift.get('verdict')}")

    pnl = virtual_pnl_report(account)
    if pnl:
        lines.append(f"仮想損益: NAV {pnl['starting_nav']:,.0f}→{pnl['current_nav']:,.0f}  "
                     f"累積リターン{pnl['total_return']*100:+.2f}%  "
                     f"最大DD{pnl['max_drawdown']*100:.2f}%  "
                     f"約定{pnl['n_fills']}回  総コスト{pnl['total_cost']:,.0f}")

    uptime = system_uptime_report(run_id)
    lines.append(f"システム稼働状況: {uptime['verdict']}  "
                f"(イベント総数{uptime['n_events']}件)")

    return "\n".join(lines)
