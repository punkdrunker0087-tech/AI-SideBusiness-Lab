"""1. リスク予算 & 制約チェック ―― 「どれだけ損を許容するか」を先に定義。

階層（ポジション / 戦略 / ポートフォリオ）ごとに上限を持ち、現状が
上限を破っていないか判定する。VaR も計算する。
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass
class RiskLimits:
    max_position_weight: float = 0.20     # 単一ポジションの上限（対NAV）
    max_gross_exposure: float = 1.50      # 総エクスポージャー上限
    max_net_exposure: float = 1.00        # 純エクスポージャー上限（絶対値）
    max_portfolio_vol: float = 0.15       # 年率ボラ上限
    max_daily_var99: float = 0.03         # 日次99% VaR 上限（対NAV）
    max_drawdown: float = 0.15            # 最大DD上限


def parametric_var(returns: pd.Series, weights: pd.Series = None,
                   confidence: float = 0.99, horizon_days: int = 1) -> float:
    """パラメトリックVaR（正規近似）。返り値は正の損失率。

    returns がポートフォリオ日次リターンなら weights 不要。
    銘柄別リターンDataFrame＋weights を渡すとポートフォリオ化して計算。
    """
    from scipy.stats import norm

    if isinstance(returns, pd.DataFrame):
        w = weights.reindex(returns.columns).fillna(0.0)
        port = returns @ w
    else:
        port = returns
    mu, sd = port.mean(), port.std()
    z = norm.ppf(confidence)
    var = -(mu * horizon_days - z * sd * np.sqrt(horizon_days))
    return float(max(var, 0.0))


def historical_var(port_returns: pd.Series, confidence: float = 0.99) -> float:
    """ヒストリカルVaR（分布の裾を直接使う。正規を仮定しない）。返り値は正の損失率。"""
    q = np.percentile(port_returns.dropna(), (1 - confidence) * 100)
    return float(max(-q, 0.0))


def check(weights: pd.Series, returns: pd.DataFrame, limits: RiskLimits,
          current_drawdown: float = 0.0) -> pd.DataFrame:
    """各制約について 現状値 / 上限 / 判定 を返す。"""
    import sizing

    cov = sizing.ann_cov(returns)
    pvol = sizing.portfolio_vol(weights, cov)
    gross = float(weights.abs().sum())
    net = float(weights.sum())
    var99 = parametric_var(returns, weights)
    max_w = float(weights.abs().max())

    rows = [
        ("単一ポジション上限", max_w, limits.max_position_weight),
        ("総エクスポージャー", gross, limits.max_gross_exposure),
        ("純エクスポージャー(|net|)", abs(net), limits.max_net_exposure),
        ("年率ボラ", pvol, limits.max_portfolio_vol),
        ("日次99% VaR", var99, limits.max_daily_var99),
        ("現在ドローダウン", abs(current_drawdown), limits.max_drawdown),
    ]
    df = pd.DataFrame(rows, columns=["項目", "現状", "上限"])
    df["違反"] = df["現状"] > df["上限"]
    return df
