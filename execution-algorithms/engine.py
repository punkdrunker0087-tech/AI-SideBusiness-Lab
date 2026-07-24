"""執行エンジン ―― スケジュール(各時間刻みの発注数量)を合成市場に対して実行する。

TWAP・VWAP・アイスバーグはいずれも「スケジュールの決め方」が違うだけで、
執行のシミュレーション自体はこのエンジンを共有する。

各刻みでの約定価格 = 仲値 + スプレッド半分（買い越しならスプレッドを渡る）
                     + 一時的インパクト
恒久的インパクトはその刻み以降の仲値へ累積的に反映する（自分の売買が
市場に与えた影響を、その後の執行にも波及させる）。
"""
from dataclasses import dataclass, field

import numpy as np

import impact_model
import market_sim


@dataclass
class ExecutionResult:
    schedule: np.ndarray          # 各刻みの発注数量（+買い/−売り）
    filled: np.ndarray             # 各刻みの約定数量（参加率上限で未達のことがある）
    exec_price: np.ndarray         # 各刻みの約定価格
    mid_with_impact: np.ndarray     # 自分のインパクトを反映した後の仲値パス
    arrival_price: float           # 執行開始時点の仲値（ベンチマーク）


def simulate_execution(session: market_sim.MarketSession, schedule: np.ndarray,
                       impact_params: impact_model.ImpactParams = None,
                       max_participation: float = 0.3) -> ExecutionResult:
    """スケジュール通りに執行し、インパクトを反映しながら約定価格を決める。

    max_participation: その刻みの市場出来高に対する参加率の上限。これを
    超える発注は上限まで削られ、残数量は約定できない（約定の確実性の
    トレードオフを表現）。
    """
    impact_params = impact_params or impact_model.ImpactParams()
    n = session.n_steps
    mid = session.mid.copy()  # このコピーへ恒久的インパクトを累積する
    filled = np.zeros(n)
    exec_price = np.full(n, np.nan)
    sigma_step = np.std(np.diff(np.log(session.mid))) if n > 1 else 0.001

    for t in range(n):
        want = schedule[t]
        if want == 0:
            continue
        cap = max_participation * session.volume[t]
        qty = np.sign(want) * min(abs(want), cap)
        filled[t] = qty

        temp = impact_model.temporary_impact(qty, session.volume[t], sigma_step, impact_params)
        perm = impact_model.permanent_impact(qty, session.volume[t], sigma_step, impact_params)

        half_spread_cost = np.sign(qty) * session.spread[t] / 2.0
        exec_price[t] = mid[t] * (1 + temp) + half_spread_cost

        # 恒久的インパクトは以降の仲値パスに累積的に反映する
        mid[t:] *= (1 + perm)

    arrival_price = session.mid[0]
    return ExecutionResult(schedule, filled, exec_price, mid, arrival_price)
