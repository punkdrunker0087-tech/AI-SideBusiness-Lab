"""統計的アービトラージの通しデモ（実データ・同業種ペア）。

ペア探索 → コインテグレーション検定(二変量・多変量) → スプレッド分析
→ 平均回帰速度 → ウォークフォワード売買 → レジーム監視 → 複数ペア管理
"""
import numpy as np
import pandas as pd

import cointegration
import data_util
import meanreversion
import pair_search
import portfolio
import regime
import spread as spread_mod


def main():
    print("パネル・業種取得中…")
    close, volume = data_util.build_panel(range_="5y")
    sectors = data_util.fetch_sectors()
    print(f"  期間 {close.index[0].date()}〜{close.index[-1].date()}  {close.shape[1]}銘柄\n")

    # --- ペア候補探索 ---
    print("=" * 70)
    print("ペア候補の探索（同一業種・流動性・相関でスクリーニング）")
    print("=" * 70)
    cands = pair_search.candidate_pairs(close, volume, sectors, min_corr=0.5)
    print(cands.round(3).to_string(index=False) if not cands.empty else "候補なし")

    if cands.empty:
        print("候補ペアが見つからないため終了します。")
        return

    # --- コインテグレーション検定（全候補） ---
    print("\n" + "=" * 70)
    print("コインテグレーション検定（Engle-Granger・二変量）")
    print("=" * 70)
    eg_results = {}
    for _, row in cands.iterrows():
        a, b = row["銘柄A"], row["銘柄B"]
        res = cointegration.engle_granger(close[a], close[b])
        eg_results[(a, b)] = res
        flag = "○ コインテグレーション" if cointegration.is_cointegrated(res) else "× 非定常"
        print(f"  {a} - {b}: p値={res['p_value']:.3f}  ヘッジ比率={res['hedge_ratio']:.3f}  "
              f"→ {flag}")

    coint_pairs = [(a, b) for (a, b), r in eg_results.items() if cointegration.is_cointegrated(r)]
    if not coint_pairs:
        print("\n  コインテグレーション関係が確認できたペアなし。相関だけでは"
              "長期的関係の証拠にならないことを示す結果。best correlationペアで以降を続行。")
        best = cands.iloc[0]
        coint_pairs = [(best["銘柄A"], best["銘柄B"])]

    # --- 多変量（Johansen）: 同業種3銘柄以上のグループがあれば検証 ---
    print("\n" + "=" * 70)
    print("コインテグレーション検定（Johansen・多変量）")
    print("=" * 70)
    for industry, group in sectors.groupby(sectors):
        members = [c for c in group.index if c in close.columns]
        if len(members) >= 3:
            jres = cointegration.johansen_test(close[members])
            print(f"  {industry}（{', '.join(members)}）: "
                 f"コインテグレーション関係の本数(rank)={jres['rank']} / "
                 f"最大可能本数={len(members)-1}")

    # --- スプレッド分析・平均回帰速度（コインテグレーションペアの先頭） ---
    a, b = coint_pairs[0]
    res = eg_results[(a, b)]
    print("\n" + "=" * 70)
    print(f"スプレッド分析・平均回帰速度: {a} - {b}")
    print("=" * 70)
    sp = spread_mod.build_spread(close[a], close[b], res["hedge_ratio"], res["alpha"])
    stats = spread_mod.spread_stats(sp)
    hl = spread_mod.half_life(sp)
    print(f"  長期平均={stats['mean']:.2f}  標準偏差={stats['std']:.2f}  "
          f"1次自己相関={stats['autocorr_1']:.3f}")
    print(f"  平均回帰速度θ={hl['theta']:.4f}  半減期={hl['half_life_days']:.1f}日"
          f"（θ≤0なら∞=戻らない）")

    # --- レジーム監視 ---
    print("\n" + "=" * 70)
    print("レジーム変化: ローリング・コインテグレーション監視")
    print("=" * 70)
    sb = regime.structural_break_report(sp)
    print(f"  直近p値={sb.get('recent_pvalue', np.nan):.3f}  "
          f"以前の中央値p値={sb.get('earlier_median_pvalue', np.nan):.3f}  "
          f"ボラ比={sb.get('vol_ratio', np.nan):.2f}")
    print(f"  → {sb['verdict']}")

    # --- ウォークフォワード売買バックテスト（コインテグレーション上位2ペア） ---
    print("\n" + "=" * 70)
    print("ウォークフォワード売買バックテスト（Zスコア戦略・四半期ヘッジ比率更新）")
    print("=" * 70)
    pair_pnls = {}
    for a2, b2 in coint_pairs[:2]:
        bt = meanreversion.backtest(close[a2], close[b2])
        pair_pnls[f"{a2}-{b2}"] = bt["net_pnl_cum"]
        print(f"  {a2}-{b2}: 取引{bt['n_trades']}回  "
              f"総PnL(粗){bt['total_gross_pnl']:+.1f}  コスト{bt['total_cost']:.1f}  "
              f"総PnL(純){bt['total_net_pnl']:+.1f}  日次Sharpe{bt['sharpe_daily']:+.3f}")

    # --- 複数ペア管理 ---
    print("\n" + "=" * 70)
    print("複数ペアの管理")
    print("=" * 70)
    print(portfolio.portfolio_report(coint_pairs[:2], sectors, pair_pnls))

    print(
        "\n注意: 25銘柄未満の小規模ユニバースでの実演。コインテグレーションは"
        "\n『過去に定常だった』ことの検定であり、将来の継続を保証しない"
        "\n（レジーム監視が示す通り）。取引コストを含めても有効かを必ず確認すること。"
    )


if __name__ == "__main__":
    main()
