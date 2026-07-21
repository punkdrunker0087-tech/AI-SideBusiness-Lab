"""3. 損失管理 ―― 損切りを複数種類重ね、一つのルールへの依存を減らす。

4種類のストップを実装し、建玉後の価格系列に対して「最初にどれが発火したか」を返す。
  - price_stop  : エントリーから固定%下落
  - atr_stop    : エントリーから ATR×倍率 下落（ボラティリティベース）
  - time_stop   : 一定営業日を経過
  - signal_stop : シグナルが消えた（例: スコアが閾値割れ）
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class StopConfig:
    price_pct: float = 0.10        # 固定%ストップ
    atr_mult: float = 2.0          # ATR倍率
    atr_window: int = 14
    time_days: int = 20            # タイムストップ
    use_price: bool = True
    use_atr: bool = True
    use_time: bool = True
    use_signal: bool = True


def _atr(close: pd.Series, window: int) -> pd.Series:
    return close.diff().abs().rolling(window).mean()


def evaluate(close: pd.Series, entry_idx: int, cfg: StopConfig,
             signal: pd.Series = None) -> dict:
    """entry_idx でロング開始したとして、最初に発火するストップを返す。

    signal: Trueの間シグナル有効。Falseになったら signal_stop（省略時は無効）。
    返り値: {"stop_type": ..., "exit_idx": ..., "exit_price": ..., "pnl_pct": ...}
    """
    entry_price = close.iloc[entry_idx]
    atr = _atr(close, cfg.atr_window)
    candidates = []  # (exit_idx, type)

    for j in range(entry_idx + 1, len(close)):
        px = close.iloc[j]
        if cfg.use_price and px <= entry_price * (1 - cfg.price_pct):
            candidates.append((j, "price_stop")); break
        if cfg.use_atr and not np.isnan(atr.iloc[j]) and px <= entry_price - cfg.atr_mult * atr.iloc[j]:
            candidates.append((j, "atr_stop")); break
        if cfg.use_time and (j - entry_idx) >= cfg.time_days:
            candidates.append((j, "time_stop")); break
        if cfg.use_signal and signal is not None and not bool(signal.iloc[j]):
            candidates.append((j, "signal_stop")); break

    if not candidates:
        j = len(close) - 1
        stop_type = "no_stop(期末)"
    else:
        j, stop_type = candidates[0]

    exit_price = close.iloc[j]
    return {
        "stop_type": stop_type,
        "exit_idx": j,
        "exit_price": float(exit_price),
        "holding_days": j - entry_idx,
        "pnl_pct": float(exit_price / entry_price - 1),
    }
