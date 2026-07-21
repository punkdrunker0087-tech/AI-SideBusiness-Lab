"""Polymarketシグナル研究 CLI。

Polymarketの市場を1つ選び、対応する合法的な金融商品(既定: ドル円)との
先行・遅行関係を実データで検証する。賭けは一切行わない読み取り専用ツール。

使い方:
  # Fed金利市場の一覧を見る
  python research.py --list --keyword Fed

  # 出来高トップのFed市場 と ドル円 の関係を分析
  python research.py --keyword Fed --symbol USDJPY=X

  # 市場を条件ID(またはYESトークンID)で直接指定
  python research.py --token <yes_token_id> --symbol ^N225
"""
import argparse
import sys

import analyze
import market_source
import polymarket_source as pm


def cmd_list(keyword: str) -> None:
    markets = pm.search_markets(keyword=keyword)
    if not markets:
        print(f"キーワード '{keyword}' に一致する市場が見つかりませんでした。")
        return
    print(f"'{keyword}' に一致する市場(出来高順):\n")
    for i, m in enumerate(markets[:20]):
        print(f"[{i}] {m.volume_usd/1e6:6.1f}M | {m.question[:70]}")
        print(f"      yes_token={m.yes_token_id}")


def cmd_analyze(args) -> None:
    if args.token:
        yes_token = args.token
        title = f"(token {yes_token[:12]}…)"
    else:
        markets = pm.search_markets(keyword=args.keyword)
        if not markets:
            print(f"キーワード '{args.keyword}' に一致する市場がありません。")
            sys.exit(1)
        chosen = markets[args.index]
        yes_token = chosen.yes_token_id
        title = chosen.question
        print(f"対象市場: {title}")
        print(f"出来高: {chosen.volume_usd/1e6:.1f}M USD / 終了: {chosen.end_date}\n")

    print(f"Polymarket確率を取得中(interval={args.interval})…")
    poly_hist = pm.price_history(yes_token, interval=args.interval, fidelity=args.fidelity)
    print(f"  → {len(poly_hist)}点")

    print(f"{args.symbol} の価格を取得中…")
    mkt_hist = market_source.price_history(
        args.symbol, range_=args.range, interval=args.mkt_interval
    )
    print(f"  → {len(mkt_hist)}点\n")

    df = analyze.align(poly_hist, mkt_hist, freq=args.freq)
    if df.empty:
        print("整列後のデータが空です。両系列の期間が重なっていない可能性があります。")
        sys.exit(1)

    if args.save:
        df.to_csv(args.save)
        print(f"整列済みデータを保存: {args.save}\n")

    try:
        result = analyze.lead_lag(df, max_lag=args.max_lag)
    except ValueError as e:
        print(f"分析不可: {e}")
        sys.exit(1)

    print("=" * 60)
    print(f"Polymarket [{title[:40]}]  vs  {args.symbol}")
    print("=" * 60)
    print(analyze.interpret(result))


def main() -> None:
    p = argparse.ArgumentParser(description="Polymarketシグナル研究(読み取り専用)")
    p.add_argument("--list", action="store_true", help="市場一覧を表示して終了")
    p.add_argument("--keyword", default="Fed", help="Polymarket市場の検索語")
    p.add_argument("--index", type=int, default=0, help="一致市場の何番目を使うか")
    p.add_argument("--token", default="", help="YESトークンIDを直接指定")
    p.add_argument("--symbol", default="USDJPY=X", help="Yahoo Financeシンボル")
    p.add_argument("--interval", default="1m", help="Polymarket履歴の範囲(1m/1w/1d/max)")
    p.add_argument("--fidelity", type=int, default=60, help="Polymarketサンプル間隔(分)")
    p.add_argument("--range", default="1mo", help="金融商品の取得範囲(5d/1mo/3mo)")
    p.add_argument("--mkt-interval", default="1h", help="金融商品のサンプル間隔")
    p.add_argument("--freq", default="1h", help="整列グリッドの間隔")
    p.add_argument("--max-lag", type=int, default=12, help="相互相関の最大ラグ(時間)")
    p.add_argument("--save", default="", help="整列済みデータのCSV保存先")
    args = p.parse_args()

    if args.list:
        cmd_list(args.keyword)
    else:
        cmd_analyze(args)


if __name__ == "__main__":
    main()
