"""パフォーマンス分析 ―― リターンを資産配分・個別選択・タイミング・コストに分解する。

⚠️ 本フレームワークは資産クラスごとに単一のETFを使うため、**個別選択効果は
構造的にゼロ**になる（同一クラス内で銘柄を選ぶ余地がないため）。複数銘柄を
扱う場合にのみ意味を持つ項目として、その旨を明示した上で0として扱う。
"""
import numpy as np
import pandas as pd


def asset_contribution(weights_history: np.ndarray, returns: pd.DataFrame) -> pd.Series:
    """各資産クラスの、期間トータルリターンへの寄与（近似: 平均加重×資産リターン）。"""
    avg_weights = weights_history.mean(axis=0)
    total_return_by_asset = (1 + returns).prod() - 1
    contrib = avg_weights * total_return_by_asset.values
    return pd.Series(contrib, index=returns.columns, name="寄与")


def allocation_effect(w_portfolio: np.ndarray, w_benchmark: np.ndarray,
                      benchmark_returns: pd.Series) -> float:
    """配分効果: ベンチマークと異なる配分にしたことによる超過リターン
    （両者ともベンチマークのリターンを使う＝銘柄選択の影響を排除）。
    """
    return float(np.sum((w_portfolio - w_benchmark) * benchmark_returns.values))


def timing_effect(static_weights_return: float, rebalanced_return: float) -> float:
    """タイミング効果: 静的Buy&Hold（初期配分から放置）と、リバランスした場合の
    リターン差。いつ・どれだけ配分を戻したかという意思決定の影響を表す。
    """
    return rebalanced_return - static_weights_return


def full_attribution(weights_history: np.ndarray, returns: pd.DataFrame,
                     benchmark_weights: np.ndarray, static_total_return: float,
                     rebalanced_total_return: float, total_cost: float) -> pd.DataFrame:
    """資産配分・個別選択・タイミング・コストへの分解を1枚にまとめる。"""
    total_return_by_asset = (1 + returns).prod() - 1
    avg_weights = weights_history.mean(axis=0)

    alloc = allocation_effect(avg_weights, benchmark_weights, total_return_by_asset)
    timing = timing_effect(static_total_return, rebalanced_total_return)

    rows = [
        {"要因": "資産配分効果(vs 等ウェイト)", "値": alloc},
        {"要因": "個別選択効果", "値": 0.0, "備考": "資産クラスごと単一ETFのため構造的に0"},
        {"要因": "タイミング効果(放置 vs リバランス)", "値": timing},
        {"要因": "取引コスト", "値": -abs(total_cost)},
    ]
    return pd.DataFrame(rows)
