"""平均回帰 ―― Zスコアに基づく売買ルールをウォークフォワードで検証する。

先読み防止の2点:
  1. ヘッジ比率は「trueに全期間」ではなく、過去`lookback`日だけを使って
     定期的に再推定し（`recalib_freq`）、その値を次回再推定まで使う
  2. 売買シグナルのZスコアは、過去`z_window`日のローリング平均・標準偏差
     から計算する（未来のスプレッド分布を参照しない）
"""
import numpy as np
import pandas as pd

import cointegration


def rebalance_dates(index: pd.DatetimeIndex, freq: str) -> list:
    """実際の最終取引日を返す（暦日ラベルの非取引日問題を回避）。"""
    s = pd.Series(index, index=index)
    return s.resample(freq).last().dropna().tolist()


def walk_forward_hedge_ratio(y: pd.Series, x: pd.Series, recalib_freq: str = "QE",
                             lookback: int = 252) -> pd.Series:
    """時点ごとのヘッジ比率（recalib_freq毎に過去lookback日で再推定、step関数）。"""
    df = pd.concat([y, x], axis=1).dropna()
    dates = rebalance_dates(df.index, recalib_freq)
    beta_series = pd.Series(np.nan, index=df.index)
    for d in dates:
        window = df.loc[:d].iloc[-lookback:]
        if len(window) < 30:
            continue
        res = cointegration.engle_granger(window.iloc[:, 0], window.iloc[:, 1])
        beta_series.loc[d] = res["hedge_ratio"]
    return beta_series.ffill()


def backtest(y: pd.Series, x: pd.Series, recalib_freq: str = "QE", lookback: int = 252,
            z_window: int = 20, entry_z: float = 2.0, exit_z: float = 0.5,
            cost_bps: float = 15.0) -> dict:
    """ウォークフォワードでヘッジ比率を更新しながらZスコア戦略を検証する。"""
    beta = walk_forward_hedge_ratio(y, x, recalib_freq, lookback)
    df = pd.concat([y, x, beta.rename("beta")], axis=1).dropna()
    spread = df.iloc[:, 0] - df["beta"] * df.iloc[:, 1]

    roll_mean = spread.rolling(z_window).mean()
    roll_std = spread.rolling(z_window).std()
    z = (spread - roll_mean) / roll_std.replace(0, np.nan)

    position = pd.Series(0.0, index=spread.index)  # +1: スプレッドをロング, -1: ショート
    pos = 0.0
    for i in range(1, len(z)):
        zi = z.iloc[i]
        if np.isnan(zi):
            position.iloc[i] = pos
            continue
        if pos == 0:
            if zi > entry_z:
                pos = -1.0
            elif zi < -entry_z:
                pos = 1.0
        else:
            if abs(zi) < exit_z:
                pos = 0.0
        position.iloc[i] = pos

    spread_change = spread.diff().fillna(0.0)
    gross_pnl = position.shift(1).fillna(0.0) * spread_change
    turnover = position.diff().abs().fillna(0.0)
    notional = df.iloc[:, 0].abs() + df["beta"].abs() * df.iloc[:, 1].abs()
    cost = turnover * notional * (cost_bps / 1e4)
    net_pnl = gross_pnl - cost

    n_trades = int((position.diff().abs() > 0).sum())
    return {
        "spread": spread, "z_score": z, "position": position,
        "gross_pnl_cum": gross_pnl.cumsum(), "net_pnl_cum": net_pnl.cumsum(),
        "n_trades": n_trades, "total_net_pnl": float(net_pnl.sum()),
        "total_gross_pnl": float(gross_pnl.sum()), "total_cost": float(cost.sum()),
        "sharpe_daily": float(net_pnl.mean() / net_pnl.std()) if net_pnl.std() else np.nan,
    }
