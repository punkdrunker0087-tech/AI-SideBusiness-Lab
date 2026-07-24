"""継続的なモニタリング ―― 執行アルゴリズムの日次パフォーマンスを追跡し、異常を検知する。

複数日（複数シミュレーション）にわたりTCA指標を記録し、トレンド・閾値超えを
監視する。市場構造・流動性の変化に伴う劣化を早期に検知することが目的。
"""
import numpy as np
import pandas as pd


def run_multi_day(algo_fn, n_days: int = 20, seed0: int = 100) -> pd.DataFrame:
    """同じ執行アルゴリズムを複数日分（複数シード）走らせ、TCA指標を記録する。

    algo_fn: seed -> tca.TCAReport を返す関数
    """
    rows = []
    for i in range(n_days):
        r = algo_fn(seed0 + i)
        rows.append({
            "day": i, "fill_rate": r.fill_rate,
            "implementation_shortfall_bps": r.implementation_shortfall_bps,
            "spread_cost_bps": r.spread_cost_bps,
            "impact_cost_bps": r.impact_cost_bps,
            "delay_cost_bps": r.delay_cost_bps,
            "opportunity_cost_bps": r.opportunity_cost_bps,
            "market_drift_bps": r.market_drift_bps,
            "vwap_benchmark_bps": r.vwap_benchmark_bps,
        })
    return pd.DataFrame(rows)


def monitor_alerts(history: pd.DataFrame, fill_rate_min: float = 0.95,
                   vwap_alert_bps: float = 15.0, trend_window: int = 5) -> list:
    """監視項目ごとにアラートを生成する。

    - 約定率: 計画どおり成立しているか（閾値割れ）
    - 対VWAP: 想定コストを超えていないか（絶対値の閾値超え）。IS(到着価格基準)は
      執行期間中の市場ドリフトを丸ごと含み単独では非常にノイジーなため、
      執行スキルの監視にはVWAPベンチマークの方を主指標にする
    - トレンド: 直近window日の平均が、それ以前の平均より悪化しているか
    """
    alerts = []
    latest = history.iloc[-1]

    if latest["fill_rate"] < fill_rate_min:
        alerts.append(f"⚠️ 約定率が低下: {latest['fill_rate']*100:.1f}% "
                      f"(基準{fill_rate_min*100:.0f}%)")

    if abs(latest["vwap_benchmark_bps"]) > vwap_alert_bps:
        alerts.append(f"⚠️ 対VWAPコストが基準超過: "
                      f"{latest['vwap_benchmark_bps']:+.1f}bps "
                      f"(基準±{vwap_alert_bps}bps)")

    if len(history) > trend_window * 2:
        recent = history["impact_cost_bps"].iloc[-trend_window:].mean()
        earlier = history["impact_cost_bps"].iloc[:-trend_window].mean()
        if recent > earlier * 1.5 and recent > 1.0:
            alerts.append(f"⚠️ マーケットインパクトコストが悪化トレンド: "
                          f"直近平均{recent:.1f}bps ← 以前平均{earlier:.1f}bps"
                          "（市場流動性の低下を疑う）")

    if not alerts:
        alerts.append("○ 全項目、基準内")
    return alerts


def summary_report(history: pd.DataFrame) -> str:
    lines = ["=== 執行モニタリング・サマリ ==="]
    lines.append(f"観測日数: {len(history)}")
    for col in ["fill_rate", "implementation_shortfall_bps", "vwap_benchmark_bps",
               "impact_cost_bps", "spread_cost_bps", "market_drift_bps"]:
        lines.append(f"  {col:32s} 平均={history[col].mean():+.3f}  "
                     f"標準偏差={history[col].std():.3f}")
    lines.append("\nアラート:")
    for a in monitor_alerts(history):
        lines.append(f"  {a}")
    return "\n".join(lines)
