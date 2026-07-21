"""バックテストエンジンと成績指標。

先読みバイアスを避けるため、close[t] で決めたポジションは *翌日* の
リターンに適用する（positions.shift(1)）。ポジション変更時には取引コストを
差し引く（楽天証券の国内株はゼロコースなら手数料0だが、スプレッド/
スリッページを保守的にbpsで見込む）。
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass
class Result:
    equity: pd.Series
    returns: pd.Series      # コスト差引後の日次リターン
    positions: pd.Series
    n_trades: int


def run(df: pd.DataFrame, positions: pd.Series, cost_bps: float = 5.0) -> Result:
    """OHLCV とポジションからバックテストを実行する。

    cost_bps: 片道の取引コスト（bps）。往復ではなく、ポジション変化量に対して課金。
    """
    close = df["close"]
    day_ret = close.pct_change().fillna(0.0)
    pos = positions.reindex(close.index).fillna(0.0)

    held = pos.shift(1).fillna(0.0)          # 前日終値で決めた建玉を今日に適用
    gross = held * day_ret

    turnover = pos.diff().abs()
    turnover.iloc[0] = abs(pos.iloc[0])       # 初日の建て分
    cost = turnover.fillna(0.0) * (cost_bps / 1e4)

    net = gross - cost
    equity = (1 + net).cumprod()
    n_trades = int((pos.diff().abs() > 0).sum())
    return Result(equity=equity, returns=net, positions=pos, n_trades=n_trades)


def metrics(result: Result) -> dict:
    """成績指標を辞書で返す。"""
    ret = result.returns
    equity = result.equity
    n = len(ret)
    years = n / TRADING_DAYS if n else np.nan

    total_return = float(equity.iloc[-1] - 1) if n else np.nan
    cagr = float(equity.iloc[-1] ** (1 / years) - 1) if years and years > 0 else np.nan
    vol = float(ret.std() * np.sqrt(TRADING_DAYS)) if n else np.nan
    mean_ann = ret.mean() * TRADING_DAYS
    sharpe = float(mean_ann / vol) if vol and vol > 0 else np.nan

    roll_max = equity.cummax()
    drawdown = equity / roll_max - 1
    max_dd = float(drawdown.min()) if n else np.nan

    in_pos = result.positions.shift(1).fillna(0) > 0
    pos_days = ret[in_pos]
    win_rate = float((pos_days > 0).mean()) if len(pos_days) else np.nan
    exposure = float(in_pos.mean()) if n else np.nan

    return {
        "total_return": total_return,
        "cagr": cagr,
        "vol": vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "exposure": exposure,
        "n_trades": result.n_trades,
        "n_days": n,
    }


def _fmt(value, spec, scale=1.0):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return " —  "
    return format(value * scale, spec)


def format_metrics(m: dict) -> str:
    return (
        f"総リターン {_fmt(m['total_return'], '+6.1f', 100)}%  "
        f"CAGR {_fmt(m['cagr'], '+5.1f', 100)}%  "
        f"Sharpe {_fmt(m['sharpe'], '+.2f')}  "
        f"最大DD {_fmt(m['max_drawdown'], '6.1f', 100)}%  "
        f"勝率 {_fmt(m['win_rate'], '4.1f', 100)}%  "
        f"建玉率 {_fmt(m['exposure'], '4.0f', 100)}%  "
        f"取引 {m['n_trades']}回"
    )
