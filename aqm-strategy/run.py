"""AQM-01 v0 実行CLI（market-neutral ロング/ショート）。

代理ユニバースで合成スコアを計算し、ドルニュートラルのL/Sをバックテスト。
全期間・年次（レジーム別）・対TOPIXベータを表示する。market-neutral戦略の
本当のベンチマークは「現金(0%)」であり、低ベータで正のリターンが出るかを見る。

使い方:
  python run.py
  python run.py --top-q 0.2 --rebalance ME --cost-bps 15 --borrow-bps 100
"""
import argparse

import numpy as np
import pandas as pd

import panel
import strategy


def main():
    p = argparse.ArgumentParser(description="AQM-01 v0 バックテスト")
    p.add_argument("--range", default="5y", help="取得期間(2y/5y/max)")
    p.add_argument("--top-q", type=float, default=0.2, help="上下何割をL/Sするか")
    p.add_argument("--rebalance", default="ME", help="リバランス頻度(ME=月末/W=週次)")
    p.add_argument("--cost-bps", type=float, default=15.0, help="片道コスト(手数料+スリッページ)")
    p.add_argument("--borrow-bps", type=float, default=100.0, help="空売りコスト(年率bps)")
    p.add_argument("--no-cache", action="store_true", help="キャッシュを使わず再取得")
    args = p.parse_args()

    print("パネル構築中（代理ユニバース25銘柄）…")
    close, volume = panel.build_panel(range_=args.range, use_cache=not args.no_cache)
    bench_px = panel.benchmark_series(range_=args.range, use_cache=not args.no_cache)
    print(f"  期間: {close.index[0].date()} 〜 {close.index[-1].date()}  "
          f"銘柄数: {close.shape[1]}  営業日: {close.shape[0]}\n")

    score = strategy.composite_score(close, volume)
    res = strategy.backtest(
        close, score,
        top_q=args.top_q, rebalance=args.rebalance,
        cost_bps=args.cost_bps, borrow_bps_annual=args.borrow_bps,
    )

    bench_ret = bench_px.pct_change().reindex(res.returns.index)
    m = strategy.metrics(res.returns, res.equity, bench_ret)

    print(f"重み（Q再配分後）: M={strategy.WEIGHTS['M']:.3f} "
          f"σ={strategy.WEIGHTS['sigma']:.3f} L={strategy.WEIGHTS['L']:.3f}")
    print(f"Gross平均={res.gross.mean():.2f}  Net平均={res.net.mean():+.3f}  "
          f"（目標: Gross≈1.5, Net≈0）\n")

    print("=" * 70)
    print("全期間 成績（コスト・空売りコスト差引後）")
    print("=" * 70)
    print(f"  戦略      : {strategy.format_metrics(m)}")

    # ベンチ（TOPIX）の同期間B&H
    bench_eq = (1 + bench_ret.fillna(0)).cumprod()
    mb = strategy.metrics(bench_ret.fillna(0), bench_eq)
    print(f"  TOPIX(B&H): {strategy.format_metrics(mb)}")

    print("\n--- 年次（レジーム別）: 戦略の絶対リターン ---")
    yearly = res.returns.groupby(res.returns.index.year).apply(
        lambda r: (1 + r).prod() - 1
    )
    yearly_b = bench_ret.fillna(0).groupby(bench_ret.index.year).apply(
        lambda r: (1 + r).prod() - 1
    )
    for y in yearly.index:
        print(f"    {y}: 戦略 {yearly[y]*100:+6.1f}%   TOPIX {yearly_b.get(y, np.nan)*100:+6.1f}%")

    beta = m.get("beta_vs_bench", np.nan)
    print("\n" + "-" * 70)
    neutral = abs(beta) < 0.3 if not np.isnan(beta) else False
    print(f"対TOPIXベータ = {beta:+.2f}  → "
          + ("○ ほぼ市場ニュートラル" if neutral else "△ 中立性が不十分（β大）"))
    verdict = (
        "○ 低ベータで正のSharpe（market-neutral alphaの兆し）"
        if (not np.isnan(m["sharpe"]) and m["sharpe"] > 0.3 and neutral)
        else "× market-neutralな優位は確認できない"
    )
    print(f"判定: {verdict}")
    print(
        "\n注意: これはQuality抜き・25銘柄代理・単一設定の結果。"
        "\nQualityファクター欠落で設計の劣化版であり、これで戦略の可否は断定できない。"
        "\n本評価にはTOPIX500全銘柄・財務データ・複数設定でのウォークフォワードが必要。"
    )


if __name__ == "__main__":
    main()
