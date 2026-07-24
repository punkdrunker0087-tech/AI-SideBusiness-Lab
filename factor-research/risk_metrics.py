"""5. リスク評価 ―― 単純なリターンでなく、複数のリスク指標で評価する。"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def volatility(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    return float(returns.dropna().std() * np.sqrt(periods))


def downside_deviation(returns: pd.Series, mar: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """下方偏差: 最低許容リターン(MAR)を下回る変動のみで測るリスク。"""
    r = returns.dropna()
    downside = r[r < mar] - mar
    if len(downside) == 0:
        return 0.0
    return float(np.sqrt((downside ** 2).mean()) * np.sqrt(periods))


def max_drawdown(returns: pd.Series) -> float:
    equity = (1 + returns.dropna()).cumprod()
    return float((equity / equity.cummax() - 1).min())


def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    r = returns.dropna()
    excess = r.mean() * periods - rf
    vol = volatility(r, periods)
    return float(excess / vol) if vol else np.nan


def sortino_ratio(returns: pd.Series, mar: float = 0.0, periods: int = TRADING_DAYS) -> float:
    r = returns.dropna()
    excess = r.mean() * periods - mar
    dd = downside_deviation(r, mar, periods)
    return float(excess / dd) if dd else np.nan


def calmar_ratio(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    r = returns.dropna()
    n_years = len(r) / periods
    if n_years <= 0:
        return np.nan
    cagr = float((1 + r).prod() ** (1 / n_years) - 1)
    mdd = abs(max_drawdown(r))
    return float(cagr / mdd) if mdd else np.nan


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    r = returns.dropna()
    return float(-np.percentile(r, (1 - confidence) * 100))


def historical_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    r = returns.dropna()
    var = np.percentile(r, (1 - confidence) * 100)
    tail = r[r <= var]
    return float(-tail.mean()) if len(tail) else np.nan


def full_report(returns: pd.Series) -> dict:
    return {
        "volatility": volatility(returns),
        "downside_deviation": downside_deviation(returns),
        "max_drawdown": max_drawdown(returns),
        "sharpe": sharpe_ratio(returns),
        "sortino": sortino_ratio(returns),
        "calmar": calmar_ratio(returns),
        "var_95": historical_var(returns),
        "cvar_95": historical_cvar(returns),
    }
