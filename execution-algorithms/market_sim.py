"""合成市場シミュレーション ―― 執行アルゴリズムを検証するための1日分の板環境。

⚠️ 無料データには板情報・イントラデイ出来高がないため、実市場のティック
データではなく**様式化された事実（stylized facts）**に基づく合成市場を使う
（`../market-making/simulation.py`と同じ設計方針）。

- 出来高プロファイル: 寄り付き・引けに厚く、中盤で薄いU字型
  （多くの市場で観測される典型的なイントラデイ出来高パターン）
- 価格: 幾何ブラウン運動
- スプレッド: 出来高が薄い時間帯ほど広がる
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class MarketSession:
    n_steps: int          # 1日をいくつの時間刻みに分割するか（例: 78 = 5分刻み×6.5時間）
    mid: np.ndarray        # 各刻みの仲値
    volume: np.ndarray      # 各刻みの市場出来高（株数）
    spread: np.ndarray      # 各刻みのスプレッド（価格単位）


def u_shaped_profile(n_steps: int, peak_ratio: float = 3.0) -> np.ndarray:
    """寄り付き・引けに厚いU字型の出来高プロファイル（合計1に正規化）。"""
    x = np.linspace(-1, 1, n_steps)
    shape = 1 + (peak_ratio - 1) * x ** 2  # 両端で peak_ratio 倍、中央で1倍
    return shape / shape.sum()


def simulate_session(n_steps: int = 78, total_volume: float = 2_000_000,
                     mid0: float = 3000.0, sigma_daily: float = 0.02,
                     base_spread_bps: float = 5.0, seed: int = 0) -> MarketSession:
    """1日分の合成市場（仲値・出来高・スプレッド）を生成する。"""
    rng = np.random.default_rng(seed)

    vol_profile = u_shaped_profile(n_steps)
    volume = total_volume * vol_profile

    step_sigma = sigma_daily / np.sqrt(n_steps)
    rets = rng.normal(0, step_sigma, n_steps)
    mid = mid0 * np.exp(np.cumsum(rets))

    # 出来高が薄い時間帯ほどスプレッドが広がる（流動性とスプレッドの逆関係）
    liquidity_factor = vol_profile.mean() / vol_profile
    spread_bps = base_spread_bps * liquidity_factor
    spread = mid * spread_bps / 1e4

    return MarketSession(n_steps=n_steps, mid=mid, volume=volume, spread=spread)
