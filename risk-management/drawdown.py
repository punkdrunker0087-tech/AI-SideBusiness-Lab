"""4. ドローダウン管理 ―― 累積損失が閾値を超えたら段階的に対応する。

新規停止 → ポジション縮小 → 戦略レビュー、という段階制御を実装する。
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DrawdownPolicy:
    warn: float = 0.05        # 警戒：監視強化
    reduce: float = 0.10      # 縮小：エクスポージャーを削る
    halt: float = 0.15        # 停止：新規停止＋戦略レビュー
    reduce_to: float = 0.5    # reduce時に残すエクスポージャー比率


def drawdown_series(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1


def current_state(equity: pd.Series, policy: DrawdownPolicy) -> dict:
    """現在のDDと、政策に基づく推奨アクションを返す。"""
    dd = float(drawdown_series(equity).iloc[-1])
    a = abs(dd)
    if a >= policy.halt:
        action = "停止：新規発注を止め、戦略レビューを実施"
        exposure_scale = 0.0
    elif a >= policy.reduce:
        action = f"縮小：エクスポージャーを{policy.reduce_to:.0%}へ削減"
        exposure_scale = policy.reduce_to
    elif a >= policy.warn:
        action = "警戒：監視強化（サイズは維持）"
        exposure_scale = 1.0
    else:
        action = "通常運転"
        exposure_scale = 1.0
    return {"drawdown": dd, "action": action, "exposure_scale": exposure_scale}


def max_drawdown(equity: pd.Series) -> float:
    return float(drawdown_series(equity).min())
