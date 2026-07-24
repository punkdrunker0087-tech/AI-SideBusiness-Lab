"""PV-002の検証: RQ-003で使ったSpearman相関+Permutation Testは、
n=449において、どの程度の真の相関があれば検出できるか（検定力分析）。

事前登録: research_questions/pipeline_validation/PV-002_power_check.md
実データ(流動性・ratio)の周辺分布はそのまま使い、順位のみ操作して
狙った強さのSpearman相関を持つ合成ペアを作る。
"""
import os

import numpy as np
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "rq003_events_with_liquidity.csv")
RHO_TARGETS = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25]
N_SIMS = 200
N_PERM = 1000
SEED = 42
ALPHA = 0.05


def spearman_from_ranks(rank_x, rank_y):
    """順位配列(1..n)からSpearman rhoを標準公式で計算する(タイなし前提)。"""
    n = len(rank_x)
    d2 = (rank_x - rank_y) ** 2
    return 1 - 6 * d2.sum() / (n * (n**2 - 1))


def permutation_pvalue(rank_x, rank_y, rng, n_perm=N_PERM):
    n = len(rank_x)
    rho_obs = spearman_from_ranks(rank_x, rank_y)
    # ランク y をn_perm回シャッフルした行列を作り、ベクトル化して相関を計算
    rand_mat = rng.random((n_perm, n))
    perm_ranks_y = np.argsort(rand_mat, axis=1) + 1  # 各行が1..nのランダム順列
    d2 = (rank_x[None, :] - perm_ranks_y) ** 2
    null_rhos = 1 - 6 * d2.sum(axis=1) / (n * (n**2 - 1))
    p_value = (np.abs(null_rhos) >= abs(rho_obs)).mean()
    return rho_obs, p_value


def main():
    df = pd.read_csv(DATA_PATH)
    liquidity_sorted = np.sort(df["liquidity"].to_numpy())
    ratio_sorted = np.sort(df["ratio"].to_numpy())
    n = len(df)
    print(f"n = {n}")

    rng = np.random.default_rng(SEED)

    results = {}
    for rho_target in RHO_TARGETS:
        rho_pearson = 2 * np.sin(rho_target * np.pi / 6)
        cov = np.array([[1, rho_pearson], [rho_pearson, 1]])
        significant_count = 0
        achieved_rhos = []
        for _ in range(N_SIMS):
            z = rng.multivariate_normal([0, 0], cov, size=n)
            rank_z1 = np.argsort(np.argsort(z[:, 0])) + 1
            rank_z2 = np.argsort(np.argsort(z[:, 1])) + 1
            synth_liquidity = liquidity_sorted[rank_z1 - 1]
            synth_ratio = ratio_sorted[rank_z2 - 1]
            rank_liq = np.argsort(np.argsort(synth_liquidity)) + 1
            rank_ratio = np.argsort(np.argsort(synth_ratio)) + 1
            rho_obs, p_value = permutation_pvalue(rank_liq, rank_ratio, rng)
            achieved_rhos.append(rho_obs)
            if p_value < ALPHA:
                significant_count += 1
        power = significant_count / N_SIMS
        mean_achieved_rho = np.mean(achieved_rhos)
        results[rho_target] = power
        print(f"rho_target={rho_target:.2f} (実現平均rho={mean_achieved_rho:.3f}): "
              f"検出力={power:.3f} ({significant_count}/{N_SIMS})")

    print("\n--- H4判定 ---")
    power_at_015 = results[0.15]
    print(f"rho=0.15での検出力: {power_at_015:.3f}")
    print(f"H4（検出力>=0.80で支持）: {'支持' if power_at_015 >= 0.80 else '棄却'}")


if __name__ == "__main__":
    main()
