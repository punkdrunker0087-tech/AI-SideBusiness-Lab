"""マルチファクター投資フレームワークの通しデモ（実データ・25銘柄）。

1.仮説 → 3.ファクター構築 → 4.評価(IC) → 露出(エクスポージャー) →
相関(時間変化・ストレス時) → 5.リバランス → パフォーマンス分解
"""
import numpy as np
import pandas as pd

import attribution
import correlation
import data_util
import evaluation
import exposure
import factors
import hypothesis
import rebalance


def main():
    print("パネル・ファンダメンタル・セクター取得中（25銘柄・5年）…")
    close, volume = data_util.build_panel(range_="5y")
    bench = data_util.fetch_one(data_util.BENCHMARK, "5y")["close"]
    fundamentals = data_util.fetch_fundamentals()
    sectors = data_util.fetch_sectors()
    print(f"  期間 {close.index[0].date()}〜{close.index[-1].date()}  "
          f"{close.shape[1]}銘柄  ファンダメンタル取得 {fundamentals.notna().all(axis=1).sum()}銘柄\n")

    price_factors = factors.build_price_factors(close)
    snapshot_z = factors.build_snapshot_factors(fundamentals)

    # --- 1+4: 仮説とIC評価（価格ベースのMomentum/LowVolのみ正式評価）---
    print("=" * 66)
    print("Stage 1+4: 仮説設定 → IC評価（価格ベースのみ・20日先リターン）")
    print("=" * 66)
    for h in hypothesis.REGISTRY:
        print(f"\n  【{h.name}】{h.rationale[:38]}…")
        if h.data_type == "price":
            key = "momentum" if h.name == "Momentum" else "low_vol"
            s = evaluation.evaluate_price_factor(price_factors[key], close)
            print(f"    IC平均={s['ic_mean']:+.3f}  IC_IR={s['ic_ir']:+.2f}  "
                  f"勝率={s['hit_rate']*100:.0f}%  t値={s['t_stat']:+.1f}")
        else:
            print(f"    ⚠️ スナップショットのみのため時系列IC評価は先読みバイアスになり実施不可。"
                  f"\n       ライブ・エクスポージャーとしてのみ使用（下記参照）")

    # --- 露出: 現時点のファクター・エクスポージャーとセクター集中度 ---
    print("\n" + "=" * 66)
    print("露出（エクスポージャー）: 現在の等ウェイト・ポートフォリオ")
    print("=" * 66)
    all_factors_today = pd.DataFrame({
        "momentum": price_factors["momentum"].iloc[-1],
        "low_vol": price_factors["low_vol"].iloc[-1],
    }).join(snapshot_z)
    # クロスセクションZ化（露出計算のスケールを揃える）
    all_z = (all_factors_today - all_factors_today.mean()) / all_factors_today.std()
    equal_weights = pd.Series(1.0 / len(close.columns), index=close.columns)
    print(exposure.concentration_report(equal_weights, all_z, sectors))

    # --- 相関: ファクターリターンの時間変化・ストレス時 ---
    print("\n" + "=" * 66)
    print("相関と分散: Momentum × LowVol（価格ベース・月次リバランスのロング/ショート）")
    print("=" * 66)
    factor_rets = {
        "momentum": correlation.factor_return_series(price_factors["momentum"], close),
        "low_vol": correlation.factor_return_series(price_factors["low_vol"], close),
    }
    print(correlation.factor_return_correlation(factor_rets).round(3).to_string(index=False))
    market_ret = bench.pct_change().reindex(factor_rets["momentum"].index)
    print("\nストレス時（市場下位10%日）vs 平常時の相関変化:")
    print(correlation.stress_correlation(factor_rets, market_ret).round(3).to_string(index=False))

    print("\n現時点の5ファクター・スコア横断相関（銘柄選択の重複度・スナップショット含む）:")
    print(correlation.cross_sectional_factor_correlation(all_z).round(2).to_string())

    # --- リバランス: 頻度別の回転率・コストのトレードオフ ---
    print("\n" + "=" * 66)
    print("リバランス: 頻度別の回転率・コストのトレードオフ（Momentumファクター）")
    print("=" * 66)
    print(rebalance.compare_frequencies(price_factors["momentum"], close).round(4).to_string(index=False))

    # --- パフォーマンス分解 ---
    print("\n" + "=" * 66)
    print("パフォーマンス分析: リターン分解（Momentumロング・ショート、月次）")
    print("=" * 66)
    mom_ret = factor_rets["momentum"]
    rb = rebalance.rebalance_backtest(price_factors["momentum"], close, "ME")
    report = attribution.contribution_report(
        mom_ret, market_ret, {"low_vol": factor_rets["low_vol"]},
        cost_drag=rb["cost_drag"],
    )
    print(report.round(4).to_string(index=False))

    print(
        "\n注意: Value/Quality/Sizeはスナップショットのみのため、露出分析にのみ"
        "\n正当に使える（過去バックテストへの適用は先読み）。Momentum/LowVolのみ"
        "\n全期間IC評価・リバランス・パフォーマンス分解の対象とした。"
    )


if __name__ == "__main__":
    main()
