"""7. 実装可能性 ―― 取引コスト・流動性・キャパシティ・市場インパクトを評価する。

理論上のファクターリターンは無限の資金を前提とするが、実際にはポジションを
建てるほど市場インパクトが効いてくる。平方根法則（`../execution-algorithms/
impact_model.py`と同じ考え方）で、運用額（AUM）を増やしたときにインパクト
コストがファクターのエッジをどれだけ侵食するかを推定する。

  impact_bps(AUM) = η・σ・sqrt(participation_rate) を年率bpsに換算
  participation_rate = (AUM / 銘柄数) / (平均売買代金 × リバランス日数)
"""
import numpy as np
import pandas as pd


def participation_rate(position_value: float, avg_dollar_volume: float,
                       rebalance_days: int = 20) -> float:
    """リバランス期間内に売買代金の何%を占めるか（複数日に分散執行する前提）。"""
    if avg_dollar_volume <= 0:
        return np.inf
    return position_value / (avg_dollar_volume * rebalance_days)


def impact_cost_bps(position_value: float, avg_dollar_volume: float, sigma_annual: float,
                    rebalance_days: int = 20, eta: float = 0.15) -> float:
    """1ポジションあたりの市場インパクトコスト（年率bps換算・往復想定）。"""
    pr = participation_rate(position_value, avg_dollar_volume, rebalance_days)
    daily_sigma = sigma_annual / np.sqrt(252)
    impact = eta * daily_sigma * np.sqrt(pr)
    return float(impact * 1e4 * 2)  # 往復(建玉+解消)ぶん×2


def capacity_curve(avg_dollar_volumes: pd.Series, sigma_annual: pd.Series,
                   n_names: int, aum_levels: np.ndarray = None,
                   rebalance_days: int = 20) -> pd.DataFrame:
    """AUM水準ごとの平均インパクトコスト（等ウェイト配分を仮定）。"""
    # 1億円〜100兆円。超大型・超高流動性銘柄のみのユニバースでは、実際に
    # エッジの数十%が侵食される水準が兆円単位になりうるため、広めに取る。
    aum_levels = aum_levels if aum_levels is not None else np.geomspace(1e8, 1e14, 30)
    rows = []
    for aum in aum_levels:
        position_value = aum / n_names
        costs = [
            impact_cost_bps(position_value, avg_dollar_volumes[sym], sigma_annual[sym], rebalance_days)
            for sym in avg_dollar_volumes.index
        ]
        rows.append({"aum_oku": aum / 1e8, "avg_impact_bps": float(np.mean(costs)),
                    "max_impact_bps": float(np.max(costs))})
    return pd.DataFrame(rows)


def estimate_capacity(curve: pd.DataFrame, factor_edge_bps_annual: float,
                      erosion_fractions: list = (0.1, 0.25, 0.5)) -> dict:
    """ファクターの年率エッジ(bps)のうち、指定割合がインパクトコストで
    消える運用額（AUM）を推定する（キャパシティの目安）。
    """
    results = {}
    for frac in erosion_fractions:
        threshold = factor_edge_bps_annual * frac
        exceeding = curve[curve["avg_impact_bps"] >= threshold]
        aum = float(exceeding["aum_oku"].iloc[0]) if not exceeding.empty else None
        results[f"edge_{int(frac*100)}pct_eroded_at_aum_oku"] = aum
    return results
