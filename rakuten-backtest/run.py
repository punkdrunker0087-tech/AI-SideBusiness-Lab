"""バックテストCLI。

戦略を1つ選び、日本株/ETFの過去データで検証する。過学習を避けるため、
期間をイン(train)/アウト(test)に分割し、**アウトオブサンプルでバイ&ホールドを
上回るか**を最重要指標として表示する。イン側だけ良くてアウトで崩れる戦略は
「過去に当てはめただけ」であり、実運用では使えない。

使い方:
  python run.py --symbol 1321.T --strategy sma_crossover
  python run.py --symbol 7203.T --strategy momentum --lookback 60 --cost-bps 5
  python run.py --symbol 1321.T --strategy all      # 全戦略を一覧比較
"""
import argparse
import inspect

import backtest
import data
from strategies import REGISTRY


def _positions(strat_name: str, df, params: dict):
    fn = REGISTRY[strat_name]
    sig = inspect.signature(fn)
    kwargs = {k: v for k, v in params.items() if k in sig.parameters and v is not None}
    return fn(df, **kwargs)


def _run_window(df, positions, cost_bps):
    res = backtest.run(df, positions, cost_bps=cost_bps)
    return backtest.metrics(res)


def _benchmark(df, cost_bps):
    from strategies import buy_hold

    return _run_window(df, buy_hold(df), cost_bps)


def evaluate(symbol, strat_name, params, cost_bps, split, range_):
    df = data.fetch(symbol, range_=range_)
    positions = _positions(strat_name, df, params)

    cut = int(len(df) * split)
    df_tr, df_te = df.iloc[:cut], df.iloc[cut:]
    pos_tr, pos_te = positions.iloc[:cut], positions.iloc[cut:]

    full = _run_window(df, positions, cost_bps)
    tr = _run_window(df_tr, pos_tr, cost_bps)
    te = _run_window(df_te, pos_te, cost_bps)
    bh_te = _benchmark(df_te, cost_bps)

    print(f"\n■ {symbol}  戦略: {strat_name}  params={params}  cost={cost_bps}bps")
    print(f"  期間: {df.index[0].date()} 〜 {df.index[-1].date()} ({len(df)}営業日)")
    print(f"  全期間       : {backtest.format_metrics(full)}")
    print(f"  イン (train) : {backtest.format_metrics(tr)}")
    print(f"  アウト(test) : {backtest.format_metrics(te)}")
    print(f"  └ 基準:B&H   : {backtest.format_metrics(bh_te)}")

    if te["n_trades"] == 0 and te["exposure"] == 0:
        print("  判定: － アウト期間で一度も建玉せず（検証不能・条件が厳しすぎる）")
        return te, bh_te

    import numpy as np

    edge = te["total_return"] - bh_te["total_return"]
    sharpe_edge = te["sharpe"] - bh_te["sharpe"]
    se = 0.0 if np.isnan(sharpe_edge) else sharpe_edge
    verdict = (
        "○ アウトでB&Hを上回る（リターン・Sharpe両方）"
        if edge > 0 and se > 0
        else "△ 一部のみ上回る"
        if edge > 0 or se > 0
        else "× アウトでB&Hに劣る（この戦略に優位なし）"
    )
    print(
        f"  判定: {verdict}  "
        f"[超過リターン {edge*100:+.1f}%pt / 超過Sharpe {sharpe_edge:+.2f}]"
    )
    return te, bh_te


def main():
    p = argparse.ArgumentParser(description="日本株バックテスト（楽天証券想定）")
    p.add_argument("--symbol", default="1321.T", help="Yahooシンボル(例: 1321.T)")
    p.add_argument("--strategy", default="sma_crossover", help="戦略名 or 'all'")
    p.add_argument("--range", default="2y", help="取得期間(2y/5y/max)")
    p.add_argument("--cost-bps", type=float, default=5.0, help="片道取引コスト(bps)")
    p.add_argument("--split", type=float, default=0.6, help="train比率(残りをtest)")
    # 戦略パラメータ
    p.add_argument("--fast", type=int, default=None)
    p.add_argument("--slow", type=int, default=None)
    p.add_argument("--lookback", type=int, default=None)
    p.add_argument("--period", type=int, default=None)
    p.add_argument("--low", type=float, default=None)
    p.add_argument("--high", type=float, default=None)
    args = p.parse_args()

    params = {
        "fast": args.fast,
        "slow": args.slow,
        "lookback": args.lookback,
        "period": args.period,
        "low": args.low,
        "high": args.high,
    }

    names = list(REGISTRY.keys()) if args.strategy == "all" else [args.strategy]
    for name in names:
        if name == "buy_hold":
            continue
        evaluate(args.symbol, name, params, args.cost_bps, args.split, args.range)

    print(
        "\n注意: アウトオブサンプルで基準(B&H)を安定して上回って初めて意味がある。"
        "\n多くのパラメータや銘柄を試すほど『偶然の勝ち』が混じる（多重比較）。"
        "\n最終判断の前に、別銘柄・別期間で再現するか必ず確認すること。"
    )


if __name__ == "__main__":
    main()
