"""マルチアセット・ポートフォリオ最適化の通しデモ（実データ・6資産クラス・5年）。

平均分散 → 推定誤差の感応度 → ブラック・リッターマン → リスクパリティ
→ 階層的リスクパリティ → 制約 → シナリオ分析 → リバランス方針比較
→ パフォーマンス分析
"""
import numpy as np
import pandas as pd

import attribution
import black_litterman
import constraints
import data_util
import hierarchical_risk_parity as hrp
import mean_variance as mv
import rebalance
import risk_parity
import robustness

ASSET_GROUPS = {
    "1306.T": "株式", "1657.T": "株式",
    "2510.T": "債券", "1656.T": "債券",
    "1540.T": "コモディティ", "1343.T": "REIT",
}


def main():
    print("パネル取得中（6資産クラス・5年）…")
    prices = data_util.build_panel(range_="5y")
    names = [data_util.ASSETS[c] for c in prices.columns]
    returns = prices.pct_change().dropna()
    print(f"  期間 {prices.index[0].date()}〜{prices.index[-1].date()}  資産: {names}\n")

    mu = mv.expected_returns(returns)
    cov = mv.covariance(returns)
    print("年率期待リターン・ボラティリティ:")
    for name, m, v in zip(names, mu, np.sqrt(np.diag(cov))):
        print(f"  {name:20s} 期待リターン={m*100:+5.1f}%  ボラ={v*100:5.1f}%")

    # --- 1. 平均分散最適化 ---
    print("\n" + "=" * 70)
    print("1. 平均分散最適化")
    print("=" * 70)
    w_minvar = mv.min_variance_weights(cov, max_weight=0.5)
    w_maxsharpe = mv.max_sharpe_weights(mu, cov, max_weight=0.5)
    print("最小分散ポートフォリオ:", dict(zip(names, np.round(w_minvar, 3))))
    print("最大Sharpeポートフォリオ:", dict(zip(names, np.round(w_maxsharpe, 3))))

    print("\n推定誤差への感応度（ブロック・ブートストラップ200回）:")
    stability = mv.bootstrap_weight_stability(returns, n_boot=200, max_weight=0.5)
    print(robustness.weight_stability_report(stability, names).to_string())
    print("  → 標準偏差が大きいほど、推定誤差次第で配分が大きく変わりうる"
         "（平均分散最適化の古典的な弱点）")

    # --- 2. ブラック・リッターマン ---
    print("\n" + "=" * 70)
    print("2. ブラック・リッターマン")
    print("=" * 70)
    policy_weights = np.array([0.25, 0.20, 0.20, 0.10, 0.10, 0.15])  # 代用の政策配分
    pi = black_litterman.implied_equilibrium_returns(policy_weights, cov, delta=2.5)
    print("政策配分から逆算した均衡期待リターン:")
    for name, p in zip(names, pi):
        print(f"  {name:20s} {p*100:+5.1f}%")

    # 見通し: 「海外株(1657)は国内株(1306)を年率3%上回る」を確信度70%で反映
    P = np.zeros((1, len(names)))
    P[0, list(prices.columns).index("1657.T")] = 1
    P[0, list(prices.columns).index("1306.T")] = -1
    Q = np.array([0.03])
    omega = black_litterman.view_confidence_to_omega(P, cov, confidences=np.array([0.7]))
    mu_bl, cov_bl = black_litterman.combine_views(pi, cov, P, Q, omega)
    print("\n見通し反映後の期待リターン（海外株>国内株+3%・確信度70%）:")
    for name, m in zip(names, mu_bl):
        print(f"  {name:20s} {m*100:+5.1f}%")
    w_bl = mv.max_sharpe_weights(mu_bl, cov_bl, max_weight=0.5)
    print("BL反映後の最大Sharpeポートフォリオ:", dict(zip(names, np.round(w_bl, 3))))

    # --- 3. リスクパリティ ---
    print("\n" + "=" * 70)
    print("3. リスクパリティ (ERC)")
    print("=" * 70)
    w_rp = risk_parity.equal_risk_contribution(cov, max_weight=0.5)
    rc = risk_parity.risk_contribution(w_rp, cov)
    print("重み:", dict(zip(names, np.round(w_rp, 3))))
    print("リスク寄与(%):", dict(zip(names, np.round(rc / rc.sum() * 100, 1))))
    print(f"分散化比率: {risk_parity.diversification_ratio(w_rp, cov):.2f}"
         f"（平均分散の最大Sharpe: {risk_parity.diversification_ratio(w_maxsharpe, cov):.2f}）")

    # --- 4. 階層的リスクパリティ (HRP) ---
    print("\n" + "=" * 70)
    print("4. 階層的リスクパリティ (HRP)")
    print("=" * 70)
    w_hrp = hrp.hrp_weights(returns)
    print("重み:", dict(zip(names, np.round(w_hrp, 3))))
    print("\n相関行列（クラスタ構造の確認用）:")
    print(returns.corr().round(2).to_string())

    # --- 制約条件 ---
    print("\n" + "=" * 70)
    print("制約条件: グループ(資産クラス)上限40%を適用")
    print("=" * 70)
    groups = [ASSET_GROUPS[c] for c in prices.columns]
    w_maxsharpe_constrained = constraints.apply_group_limit(w_maxsharpe, groups, max_group_weight=0.4)
    print("制約前(最大Sharpe):", dict(zip(names, np.round(w_maxsharpe, 3))))
    print("制約後(株式合計40%上限):", dict(zip(names, np.round(w_maxsharpe_constrained, 3))))

    # --- シナリオ分析（相関収束・ボラ急騰） ---
    print("\n" + "=" * 70)
    print("シナリオ分析: 各手法の重みが、相関収束・ボラ急騰でどう振る舞うか")
    print("=" * 70)
    weights_by_method = {
        "最小分散": w_minvar, "最大Sharpe": w_maxsharpe,
        "リスクパリティ": w_rp, "HRP": w_hrp,
    }
    print(robustness.scenario_report(weights_by_method, cov).to_string())
    print("  → 相関収束・ボラ急騰でポートフォリオボラがどれだけ増えるか、"
         "手法間の相対的な頑健性を比較できる")

    # --- リバランス方針比較 ---
    print("\n" + "=" * 70)
    print("リバランス方針比較（HRP配分を目標に、放置/定期/閾値）")
    print("=" * 70)
    print(rebalance.compare_policies(returns, w_hrp).round(4).to_string(index=False))

    # --- パフォーマンス分析 ---
    print("\n" + "=" * 70)
    print("パフォーマンス分析: 資産配分・個別選択・タイミング・コストへの分解")
    print("=" * 70)
    static_ret = float((returns @ w_hrp + 1).prod() - 1)
    rebal = rebalance.simulate_drift(returns, w_hrp, policy="periodic", freq="QE")
    rebalanced_ret = static_ret - rebal["total_cost"]  # 簡略化: リバランス後の近似トータルリターン
    equal_w = np.ones(len(names)) / len(names)
    report = attribution.full_attribution(
        rebal["weight_history"], returns, equal_w, static_ret, rebalanced_ret, rebal["total_cost"],
    )
    print(report.round(4).to_string(index=False))

    print(
        "\n注意: 政策配分・見通し・確信度は例示であり実際の市場均衡を厳密に"
        "\n再現したものではない。個別選択効果は資産クラスごと単一ETFのため0。"
        "\n複数手法の相対比較・トレードオフの理解が目的。"
    )


if __name__ == "__main__":
    main()
