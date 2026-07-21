"""アイスバーグ注文 ―― 表示数量を制限し、大口注文の存在を推測されにくくする。

親スケジュール（TWAP/VWAP等）の各刻みの目標数量を、`display_size`以下の
「見える数量」に分割して出す想定。表示数量が小さいほど:
  - 情報漏洩が減り、恒久的インパクト（他者が察知して先回りする効果）が
    軽減される（`leak_factor`として恒久的インパクト係数に掛け合わせる）
  - 一方で、大きな目標に対し表示が小さすぎると、その刻み内で全量を
    捌ききれず約定率が下がりうる（約定の確実性とのトレードオフ）
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class IcebergConfig:
    display_size: float           # 1回に見せる数量
    fill_efficiency: float = 0.85  # 表示数量に対する実務上の充足しやすさ(0-1)


def expected_fill_rate(target_qty: float, config: IcebergConfig) -> float:
    """その刻みの目標数量に対する期待約定率。

    表示数量が目標を上回れば通常通りほぼ約定(fill_efficiencyに漸近)。
    表示数量が目標より大きく下回るほど、その刻み内で捌ききれず約定率が下がる。
    """
    if target_qty <= 0:
        return 1.0
    ratio = config.display_size / abs(target_qty)
    return float(min(1.0, config.fill_efficiency * min(ratio, 1.0) + (1 - min(ratio, 1.0)) * config.fill_efficiency * ratio))


def leak_factor(config: IcebergConfig, total_qty: float) -> float:
    """表示数量/親注文全体の比率が小さいほど、恒久的インパクトを軽減する係数(0-1)。"""
    if total_qty <= 0:
        return 1.0
    ratio = min(config.display_size / abs(total_qty), 1.0)
    # 比率が小さいほど leak_factor は小さく（インパクト軽減が大きく）なる
    return float(0.3 + 0.7 * ratio)


def apply_iceberg_schedule(parent_schedule: np.ndarray, config: IcebergConfig,
                          total_qty: float) -> tuple:
    """親スケジュールをアイスバーグ執行に変換する。

    戻り値: (実効スケジュール, 各刻みの期待約定率, 恒久的インパクトのleak_factor)
    実効スケジュールは「期待約定率を織り込んだ現実的な発注量」であり、
    未達分はその刻みでは執行されない（時間をかけて後続に回すかは親アルゴリズム
    の設計次第。本実装では単純化し、未達分は執行しない＝約定の確実性の低下
    として扱う）。
    """
    fill_rates = np.array([expected_fill_rate(q, config) for q in parent_schedule])
    effective_schedule = parent_schedule * fill_rates
    leak = leak_factor(config, total_qty)
    return effective_schedule, fill_rates, leak
