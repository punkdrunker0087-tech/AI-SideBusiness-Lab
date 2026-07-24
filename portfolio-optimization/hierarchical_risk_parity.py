"""4. 階層的リスクパリティ (HRP) ―― 資産の類似性で階層構造を作り、
共分散推定の不安定さへの耐性を高める。

López de Prado, M. (2016) "Building Diversified Portfolios that Outperform
Out-of-Sample" のアルゴリズム:

  1. 相関ベースの距離行列を作る: d_ij = sqrt(0.5・(1 − corr_ij))
  2. 階層クラスタリング（最短距離法）で資産をツリー化する
  3. クラスタリング順に資産を並べ替える（準対角化）
  4. その順序でツリーを再帰的に2分割し、各半分の分散に反比例して
     重みを配分する（再帰的二分配分）

平均分散最適化と異なり、共分散行列の**逆行列を使わない**ため、
高次元・高相関で不安定になりがちな共分散推定に対して頑健とされる。
"""
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform


def correlation_distance(corr: pd.DataFrame) -> pd.DataFrame:
    """相関行列から距離行列を作る（d=0: 完全相関, d=1: 無相関, d=sqrt(2): 完全負相関）。"""
    return np.sqrt(0.5 * (1 - corr))


def quasi_diagonalize(link: np.ndarray) -> list:
    """クラスタリング結果(linkage)から、類似資産が隣り合う順序（葉のインデックス）を得る。"""
    link = link.astype(int)
    n = link.shape[0] + 1
    sort_idx = pd.Series([link[-1, 0], link[-1, 1]])
    num_items = link[-1, 3]

    while sort_idx.max() >= n:
        sort_idx.index = range(0, sort_idx.shape[0] * 2, 2)
        df0 = sort_idx[sort_idx >= n]
        i = df0.index
        j = df0.values - n
        sort_idx[i] = link[j, 0]
        df1 = pd.Series(link[j, 1], index=i + 1)
        sort_idx = pd.concat([sort_idx, df1]).sort_index()
        sort_idx.index = range(sort_idx.shape[0])
    return sort_idx.tolist()


def _cluster_variance(cov: np.ndarray, items: list) -> float:
    """クラスタ内資産の逆分散加重ポートフォリオの分散（HRP内部で使う簡易分散）。"""
    sub_cov = cov[np.ix_(items, items)]
    inv_diag = 1.0 / np.diag(sub_cov)
    w = inv_diag / inv_diag.sum()
    return float(w @ sub_cov @ w)


def recursive_bisection(cov: np.ndarray, sorted_idx: list) -> np.ndarray:
    """準対角化された順序を再帰的に2分割し、各半分の分散に反比例して配分する。"""
    weights = pd.Series(1.0, index=sorted_idx)
    clusters = [sorted_idx]

    while clusters:
        # 各クラスタを半分に分割
        clusters = [c[i:j] for c in clusters for i, j in
                   ((0, len(c) // 2), (len(c) // 2, len(c))) if len(c) > 0]
        clusters = [c for c in clusters if len(c) > 0]
        for i in range(0, len(clusters), 2):
            if i + 1 >= len(clusters):
                continue
            left, right = clusters[i], clusters[i + 1]
            var_left = _cluster_variance(cov, left)
            var_right = _cluster_variance(cov, right)
            alloc_left = 1 - var_left / (var_left + var_right)
            weights[left] *= alloc_left
            weights[right] *= (1 - alloc_left)
        clusters = [c for c in clusters if len(c) > 1]

    return weights.sort_index().values


def hrp_weights(returns: pd.DataFrame) -> np.ndarray:
    """リターンのDataFrameからHRPの重みを計算する（元のカラム順で返す）。"""
    corr = returns.corr()
    cov = returns.cov().values
    dist = correlation_distance(corr)
    condensed = squareform(dist.values, checks=False)
    link = linkage(condensed, method="single")

    sorted_idx = quasi_diagonalize(link)
    weights_sorted = recursive_bisection(cov, sorted_idx)

    # sorted_idx順の重みを、元のカラム順に戻す
    w = np.zeros(len(sorted_idx))
    for pos, asset_idx in enumerate(sorted_idx):
        w[asset_idx] = weights_sorted[pos]
    return w
