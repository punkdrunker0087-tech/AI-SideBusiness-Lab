"""4. リターン計算 ―― コーポレートアクション調整済み系列から、目的に応じた頻度で算出する。

adjcloseを使うことで分割・配当は既に調整済み（`universe.fetch_one`参照）。
日次・月次など、分析目的に応じた頻度でリターンを再計算する。
"""
import numpy as np
import pandas as pd


def daily_returns(close: pd.DataFrame) -> pd.DataFrame:
    return close.pct_change()


def monthly_returns(close: pd.DataFrame) -> pd.DataFrame:
    """月末（実際の最終取引日）ベースの月次リターン。"""
    monthly_price = close.resample("ME").last()
    return monthly_price.pct_change()


def cumulative_return(returns: pd.Series) -> float:
    return float((1 + returns.dropna()).prod() - 1)


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    r = returns.dropna()
    n_years = len(r) / periods_per_year
    if n_years <= 0:
        return np.nan
    return float((1 + r).prod() ** (1 / n_years) - 1)
