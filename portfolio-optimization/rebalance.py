"""リバランス ―― 理想配分への近さ・取引コスト・回転率のバランスを評価する。

3つの方針を比較する:
  - リバランスなし（配分を放置し、市場変動に任せる）
  - 定期リバランス（一定間隔で理想配分に戻す）
  - 閾値リバランス（理想配分からの乖離が一定幅を超えた時だけ戻す）
"""
import numpy as np
import pandas as pd


def _rebalance_dates(index: pd.DatetimeIndex, freq: str) -> list:
    """実際の最終取引日を返す（暦日ラベルの非取引日問題を回避）。"""
    s = pd.Series(index, index=index)
    return s.resample(freq).last().dropna().tolist()


def simulate_drift(returns: pd.DataFrame, target_weights: np.ndarray,
                   policy: str = "none", freq: str = "ME", band: float = 0.05,
                   cost_bps: float = 10.0) -> dict:
    """target_weightsから出発し、方針に従って配分の推移をシミュレートする。

    policy: "none"（放置）/ "periodic"（定期）/ "band"（閾値）
    """
    assets = returns.columns
    w = pd.Series(target_weights, index=assets)
    rebal_dates = set(_rebalance_dates(returns.index, freq)) if policy == "periodic" else set()

    weight_history = []
    turnover_total = 0.0
    tracking_error_sum = 0.0

    for dt, day_ret in returns.iterrows():
        # 市場変動によるドリフト
        grown = w * (1 + day_ret)
        w = grown / grown.sum()

        drift = (w.values - target_weights)
        tracking_error_sum += np.abs(drift).sum()

        do_rebalance = False
        if policy == "periodic" and dt in rebal_dates:
            do_rebalance = True
        elif policy == "band" and np.abs(drift).max() > band:
            do_rebalance = True

        if do_rebalance:
            turnover = np.abs(target_weights - w.values).sum()
            turnover_total += turnover
            w = pd.Series(target_weights, index=assets)

        weight_history.append(w.values.copy())

    n_days = len(returns)
    avg_tracking_error = tracking_error_sum / n_days
    cost_total = turnover_total * (cost_bps / 1e4)

    return {
        "policy": policy,
        "avg_tracking_error": float(avg_tracking_error),
        "total_turnover": float(turnover_total),
        "total_cost": float(cost_total),
        "weight_history": np.array(weight_history),
    }


def compare_policies(returns: pd.DataFrame, target_weights: np.ndarray,
                     cost_bps: float = 10.0) -> pd.DataFrame:
    rows = []
    for policy, kwargs in [
        ("放置(no rebalance)", {"policy": "none"}),
        ("定期(月次)", {"policy": "periodic", "freq": "ME"}),
        ("定期(四半期)", {"policy": "periodic", "freq": "QE"}),
        ("閾値(±5%)", {"policy": "band", "band": 0.05}),
        ("閾値(±10%)", {"policy": "band", "band": 0.10}),
    ]:
        r = simulate_drift(returns, target_weights, cost_bps=cost_bps, **kwargs)
        rows.append({"方針": policy, "平均乖離": r["avg_tracking_error"],
                    "総回転率": r["total_turnover"], "総コスト": r["total_cost"]})
    return pd.DataFrame(rows)
