"""アラート ―― データ更新停止・異常値・モデル性能低下・システム障害を検知する。

⚠️ 実際のSMS/メール送信は行わない（認証情報が必要な外部サービス連携は
本デモのスコープ外）。ここでは「検知→アラートイベントとして記録→通知
関数を呼ぶ」という構造のみを実装し、`notify()`は差し替え可能な
プレースホルダーとする。
"""
import numpy as np

import data_provider
import event_log
import model_layer
import monitoring


_last_notified = {}  # (run_id, check_key) -> 直近に通知した値


def notify(message: str, severity: str = "warning", run_id: str = None):
    """実際の通知チャネル（SMS/メール等）に差し替え可能なプレースホルダー。

    本デモではログ記録＋標準出力のみ。実運用ではここでTwilio/SendGrid等の
    APIを呼ぶ（本フレームワークのスコープ外・別途認証情報が必要）。
    """
    event_log.log_event("alert", {"message": message, "severity": severity}, run_id=run_id)
    print(f"  🔔 [{severity.upper()}] {message}")


def _should_notify(run_id: str, check_key: str, value: float, min_delta: float) -> bool:
    """同じ問題が続く限り毎回通知しない（アラート疲れの防止）。

    値が前回通知時から min_delta 以上悪化した時だけ再通知する。実装時、
    重複抑制なしで同一条件のアラートが100件以上連続発報される問題を
    実際に起こして発見・修正した。
    """
    key = (run_id, check_key)
    last = _last_notified.get(key)
    if last is None or abs(value - last) >= min_delta:
        _last_notified[key] = value
        return True
    return False


def check_data_staleness(validation_result: dict, max_latency_days: int = 3, run_id: str = None):
    latency = validation_result.get("latency_days")
    if latency is not None and latency > max_latency_days:
        key = f"staleness:{validation_result['symbol']}"
        if _should_notify(run_id, key, latency, min_delta=1):
            notify(f"データ更新停止の疑い: {validation_result['symbol']}が"
                  f"{latency}日更新されていない", "critical", run_id)


def check_outliers(validation_result: dict, run_id: str = None):
    n = validation_result.get("outliers_detected", 0)
    if n > 0:
        key = f"outliers:{validation_result['symbol']}"
        if _should_notify(run_id, key, n, min_delta=1):
            notify(f"異常値検出: {validation_result['symbol']}で"
                  f"{n}件の±50%超変化", "warning", run_id)


def check_model_degradation(run_id: str = None, psi_threshold: float = 0.25):
    drift = monitoring.model_drift_report(run_id)
    psi = drift.get("psi", np.nan)
    if not np.isnan(psi) and psi > psi_threshold:
        if _should_notify(run_id, "model_drift", psi, min_delta=0.1):
            notify(f"モデル性能低下の疑い: 推論信頼度のPSI={psi:.3f}"
                  f"（閾値{psi_threshold}超）", "critical", run_id)


def check_drawdown(pnl_report: dict, max_drawdown_alert: float = 0.10, run_id: str = None):
    dd = pnl_report.get("max_drawdown")
    if dd is not None and abs(dd) > max_drawdown_alert:
        if _should_notify(run_id, "drawdown", dd, min_delta=0.02):
            notify(f"ドローダウン超過: {dd*100:.1f}%（基準{max_drawdown_alert*100:.0f}%超）",
                  "critical", run_id)


def check_system_errors(run_id: str = None):
    uptime = monitoring.system_uptime_report(run_id)
    if uptime["n_errors"] > 0:
        if _should_notify(run_id, "system_errors", uptime["n_errors"], min_delta=1):
            notify(f"システムエラー検出: {uptime['n_errors']}件", "critical", run_id)


def run_all_checks(validation_result: dict, account, run_id: str = None):
    check_data_staleness(validation_result, run_id=run_id)
    check_outliers(validation_result, run_id=run_id)
    check_model_degradation(run_id=run_id)
    check_drawdown(monitoring.virtual_pnl_report(account), run_id=run_id)
    check_system_errors(run_id=run_id)
