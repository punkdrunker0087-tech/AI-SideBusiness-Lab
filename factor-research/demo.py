"""学術的ファクター研究フレームワークの通しデモ（実データ）。

2.ユニバース構築 → 3-5.ファクター別リターン/リスク → 6.レジーム別分析
→ 7.キャパシティ分析 → 8.ポートフォリオ評価 → 9.レポート生成
"""
import numpy as np
import pandas as pd

import capacity
import factors
import portfolio_evaluation as pf
import regime_analysis
import report
import risk_metrics
import returns as ret_mod
import universe


def main():
    print("2. 投資ユニバース構築中…")
    u = universe.build_universe(range_="3y")
    print(universe.format_universe_log(u))

    symbols = list(u["raw_data"].keys())
    close = pd.DataFrame({s: df["close"] for s, df in u["raw_data"].items()}).dropna()
    volume = pd.DataFrame({s: df["volume"] for s, df in u["raw_data"].items()}).reindex(close.index)
    bench = close.mean(axis=1)  # ユニバース平均を簡易ベンチマークとする

    print(f"\nユニバース確定: {len(symbols)}銘柄  期間 {close.index[0].date()}〜{close.index[-1].date()}\n")

    # --- 3. ファクター構築 ---
    mom = factors.cross_sectional_zscore(factors.momentum(close, 120))
    fundamentals = factors.fetch_snapshot_fundamentals(symbols)
    snapshot = factors.build_snapshot_factors(fundamentals)

    factor_panels = {"momentum": mom}
    print("=" * 66)
    print("3-5. ファクター別リターン・リスク評価（momentumのみ全期間検証、"
         "他はライブ断面）")
    print("=" * 66)

    factor_results, factor_returns_dict, turnovers = {}, {}, {}
    for name, panel in factor_panels.items():
        fret, turnover = pf.factor_return_series(panel, close)
        ann_ret = ret_mod.annualized_return(fret)
        risk = risk_metrics.full_report(fret)
        factor_results[name] = {"ann_return": ann_ret, "risk": risk}
        factor_returns_dict[name] = fret
        turnovers[name] = turnover
        print(f"  [{name}] 年率リターン={ann_ret*100:+.1f}%  Sharpe={risk['sharpe']:+.2f}  "
             f"Sortino={risk['sortino']:+.2f}  Calmar={risk['calmar']:+.2f}  "
             f"最大DD={risk['max_drawdown']*100:.1f}%  VaR95={risk['var_95']*100:.2f}%")

    print("\nライブ断面（Value/Quality/Size・現在時点のみ・先読み評価は不可）:")
    print(snapshot.round(2).to_string())

    # --- 6. レジーム別分析 ---
    print("\n" + "=" * 66)
    print("6. 市場環境ごとの分析")
    print("=" * 66)
    regimes = regime_analysis.classify_regime(bench)
    regime_results = {}
    for name, fret in factor_returns_dict.items():
        reg_df = regime_analysis.performance_by_regime(fret, regimes, "trend")
        regime_results[name] = reg_df
        if not reg_df.empty:
            print(f"\n[{name}] 強気/弱気別:")
            print(reg_df[["sharpe", "max_drawdown", "n_days"]].round(3).to_string())

    # --- 7. キャパシティ分析 ---
    print("\n" + "=" * 66)
    print("7. 実装可能性（キャパシティ分析）")
    print("=" * 66)
    adv = (close * volume).mean()
    sigma = close.pct_change().std() * np.sqrt(252)
    capacity_results = {}
    for name, r in factor_results.items():
        curve = capacity.capacity_curve(adv, sigma, n_names=len(symbols))
        edge_bps = abs(r["ann_return"]) * 1e4
        cap_est = capacity.estimate_capacity(curve, edge_bps)
        capacity_results[name] = cap_est
        print(f"  [{name}] 年率エッジ={edge_bps:.0f}bps")
        for k, v in cap_est.items():
            print(f"    {k}: {'到達せず(想定AUM範囲内で十分な余裕)' if v is None else f'{v:.0f}億円'}")

    # --- 8. ポートフォリオ評価 ---
    print("\n" + "=" * 66)
    print("8. ポートフォリオ評価")
    print("=" * 66)
    corr = pf.correlation_matrix(factor_returns_dict)
    print("ファクター間相関:")
    print(corr.round(2).to_string())
    turnover_df = pf.turnover_summary(turnovers)
    print("\n年率回転率:")
    print(turnover_df.round(2).to_string(index=False))

    if len(factor_returns_dict) > 1:
        w = pf.equal_risk_weights(factor_returns_dict)
        div_ratio = pf.diversification_ratio(w, factor_returns_dict)
    else:
        div_ratio = 1.0
    portfolio_results = {"correlation": corr, "turnover": turnover_df,
                        "diversification_ratio": div_ratio}

    # --- 9. レポート生成 ---
    print("\n" + "=" * 66)
    print("9. レポート生成")
    print("=" * 66)
    md = report.build_report(universe.format_universe_log(u), factor_results,
                             regime_results, capacity_results, portfolio_results)
    out_path = "factor_research_report.md"
    with open(out_path, "w") as f:
        f.write(md)
    print(f"レポートを {out_path} に出力しました（{len(md)}文字）")

    print(
        "\n注意: Value/Quality/Sizeはスナップショットのみのため、時系列の"
        "\nリターン検証はmomentumのみ実施。統計的有意性の厳密な検定は"
        "\n`../backtest-framework/`のDSR/PBOを別途適用することを推奨。"
    )


if __name__ == "__main__":
    main()
