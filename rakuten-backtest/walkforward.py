"""ウォークフォワード分析（applied learning）。

単一のtrain/test分割は「イン期間で最良のパラメータを1つ選んだだけ」で、
そのパラメータ選択自体が過去に依存している。ウォークフォワードは:

  1. 期間を [学習窓 → 検証窓] のブロックに分ける
  2. 学習窓でパラメータを最適化する
  3. その *固定した* パラメータを、次の検証窓（未来・未見）でテストする
  4. 窓を前へずらし、再最適化 → 再テスト を繰り返す
  5. 各検証窓の結果だけを連結したものが「実運用に最も近い」成績

多くの文献が「ウォークフォワードは systematic 戦略の最低要件」とする所以。
(参照: LEARNING.md の出典)

使い方:
  python walkforward.py --symbol 1321.T --strategy sma_crossover
  python walkforward.py --symbol 7203.T --strategy momentum --range 5y
"""
import argparse
import inspect
import itertools

import numpy as np
import pandas as pd

import backtest
import data
from strategies import REGISTRY, buy_hold

# 学習窓で探索するパラメータ候補
GRIDS = {
    "sma_crossover": {"fast": [10, 20, 25, 40], "slow": [50, 75, 100, 150]},
    "momentum": {"lookback": [20, 40, 60, 120]},
    "rsi_reversion": {"period": [7, 14, 21], "low": [20, 30], "high": [70, 80]},
}


def _positions(name, df, params):
    fn = REGISTRY[name]
    sig = inspect.signature(fn)
    kw = {k: v for k, v in params.items() if k in sig.parameters}
    return fn(df, **kw)


def _combos(name):
    grid = GRIDS[name]
    keys = list(grid)
    for vals in itertools.product(*[grid[k] for k in keys]):
        params = dict(zip(keys, vals))
        if name == "sma_crossover" and params["fast"] >= params["slow"]:
            continue
        yield params


def _sharpe(df, positions, cost_bps):
    m = backtest.metrics(backtest.run(df, positions, cost_bps))
    return m["sharpe"] if not np.isnan(m["sharpe"]) else -np.inf


def walk_forward(symbol, name, range_="5y", train=252, test=63, cost_bps=15.0):
    """アンカーなし（ローリング）ウォークフォワード。検証窓は重複なし。"""
    df = data.fetch(symbol, range_=range_)
    n = len(df)
    if n < train + test:
        raise ValueError(f"データ不足: {n}日（必要 {train+test}日以上）")

    oos_pos = pd.Series(np.nan, index=df.index)
    folds = []
    start = 0
    while start + train + test <= n:
        tr = df.iloc[start : start + train]
        te_idx = df.index[start + train : start + train + test]

        best_params, best_score = None, -np.inf
        for params in _combos(name):
            s = _sharpe(tr, _positions(name, tr, params), cost_bps)
            if s > best_score:
                best_score, best_params = s, params

        # 検証窓のポジションは、ウォームアップ込みで窓全体から計算し検証区間を切り出す
        window = df.iloc[start : start + train + test]
        pos_full = _positions(name, window, best_params)
        oos_pos.loc[te_idx] = pos_full.reindex(te_idx).values
        folds.append((te_idx[0].date(), te_idx[-1].date(), best_params))
        start += test  # 検証窓ぶんだけ前進（OOSは重複しない）

    covered = oos_pos.dropna().index
    df_oos = df.loc[covered]
    strat = backtest.metrics(backtest.run(df_oos, oos_pos.loc[covered], cost_bps))
    bench = backtest.metrics(backtest.run(df_oos, buy_hold(df_oos), cost_bps))
    return folds, strat, bench, (covered[0], covered[-1])


def main():
    p = argparse.ArgumentParser(description="ウォークフォワード分析")
    p.add_argument("--symbol", default="1321.T")
    p.add_argument("--strategy", default="sma_crossover", choices=list(GRIDS))
    p.add_argument("--range", default="5y")
    p.add_argument("--train", type=int, default=252, help="学習窓(営業日)")
    p.add_argument("--test", type=int, default=63, help="検証窓(営業日)")
    p.add_argument("--cost-bps", type=float, default=15.0, help="片道コスト(bps)")
    args = p.parse_args()

    folds, strat, bench, span = walk_forward(
        args.symbol, args.strategy, args.range, args.train, args.test, args.cost_bps
    )

    print(f"\n■ ウォークフォワード: {args.symbol} / {args.strategy}")
    print(f"  学習窓{args.train}日 → 検証窓{args.test}日 / コスト{args.cost_bps}bps")
    print(f"  連結OOS期間: {span[0].date()} 〜 {span[1].date()} / フォールド数{len(folds)}\n")
    print("  各フォールドで選ばれたパラメータ:")
    for s, e, params in folds:
        print(f"    {s} 〜 {e}: {params}")

    print("\n  === 連結アウトオブサンプル成績 ===")
    print(f"  戦略      : {backtest.format_metrics(strat)}")
    print(f"  基準:B&H  : {backtest.format_metrics(bench)}")
    edge = strat["total_return"] - bench["total_return"]
    se = strat["sharpe"] - bench["sharpe"]
    se = 0.0 if np.isnan(se) else se
    verdict = (
        "○ WFでもB&Hを上回る（リターン・Sharpe両方）"
        if edge > 0 and se > 0
        else "△ 一部のみ上回る"
        if edge > 0 or se > 0
        else "× WFでB&Hに劣る（この戦略に安定した優位なし）"
    )
    print(f"  判定: {verdict}  [超過リターン {edge*100:+.1f}%pt / 超過Sharpe {se:+.2f}]")
    print(
        "\n注意: これは1銘柄・1戦略の結果。複数銘柄で同じ設定を回し、勝ちが"
        "\n偶然でないか（多重検定の水増しでないか）を必ず確認すること。"
        "\nパラメータ候補を増やすほどSharpeは楽観方向に歪む（Deflated Sharpe）。"
    )


if __name__ == "__main__":
    main()
