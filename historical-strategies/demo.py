"""歴史的に証明された投資手法を現代データで検証する通しデモ。

1. タートルズのトレンドフォロー戦略（Donchian breakout + N基準サイジング）
   を複数銘柄で検証し、単一市場での挙動を確認する
2. ウォーレン・バフェットのバリュー投資を「Buffett's Alpha」論文の
   Quality+Value+Safetyへの分解として現代データに翻訳し、レバレッジの
   効果を検証する
"""
import numpy as np
import pandas as pd

import buffett_style as bs
import data_util
import turtle_trading as tt

UNIVERSE = ["7203.T", "6758.T", "9432.T", "8306.T", "9983.T", "6098.T",
           "8035.T", "9433.T", "7974.T", "6501.T"]


def main():
    print("価格データ取得中（10銘柄・5年、OHLC）…")
    ohlc = {s: data_util.fetch_ohlc(s, "5y") for s in UNIVERSE}
    close = pd.DataFrame({s: df["close"] for s, df in ohlc.items()}).dropna()
    bench = data_util.fetch_ohlc("1306.T", "5y")["close"].reindex(close.index).ffill()
    print(f"  期間 {close.index[0].date()}〜{close.index[-1].date()}\n")

    print("=" * 70)
    print("1. タートルズのトレンドフォロー戦略（Donchian breakout・原典準拠）")
    print("=" * 70)
    rows = []
    for sym in UNIVERSE:
        res = tt.run_turtle_system(ohlc[sym])
        bh_final = 10_000_000 * ohlc[sym]["close"].iloc[-1] / ohlc[sym]["close"].iloc[0]
        wins = sum(1 for t in res.trades if t["pnl"] > 0)
        wr = wins / len(res.trades) if res.trades else np.nan
        rows.append({"銘柄": sym, "タートルズ最終資産": res.equity.iloc[-1],
                    "B&H最終資産": bh_final, "取引数": len(res.trades), "勝率": wr})
    turtle_df = pd.DataFrame(rows)
    print(turtle_df.round(2).to_string(index=False))
    n_beat_bh = (turtle_df["タートルズ最終資産"] > turtle_df["B&H最終資産"]).sum()
    print(f"\n  → タートルズがB&Hを上回った銘柄: {n_beat_bh}/{len(UNIVERSE)}")
    print("    単一の上昇トレンド銘柄では、頻繁な損切りがB&Hに劣後しやすい"
         "\n    （原典は多市場分散・大暴落からの保護が主眼。単一株・単一の"
         "\n    強気相場サンプルでの検証には限界がある）")

    print("\n" + "=" * 70)
    print("2. バフェット流バリュー投資（Quality+Value+Safety・現代データへの翻訳）")
    print("=" * 70)
    ret = close.pct_change()
    bench_ret = bench.pct_change()
    betas = pd.DataFrame({s: bs.rolling_beta(ret[s], bench_ret) for s in UNIVERSE})
    beta_now = betas.iloc[-1]

    fundamentals = bs.fetch_fundamentals(UNIVERSE)
    selection = bs.select_buffett_style(fundamentals, beta_now, top_n=5)
    print("選定銘柄（Quality+Value+Safetyスコア上位5）:")
    print(selection.round(2).to_string())

    selected_symbols = selection.index.tolist()
    print("\nレバレッジ別のパフォーマンス（選定銘柄の等ウェイト保有）:")
    for lev in [1.0, 1.5, 1.7]:
        eq = bs.backtest_concentrated_portfolio(close, selected_symbols, leverage=lev)
        dd = (eq / eq.cummax() - 1).min()
        print(f"  レバレッジ{lev}倍: 最終={eq.iloc[-1]:.2f}倍  最大DD={dd*100:.1f}%")

    universe_equal = (close.mean(axis=1) / close.mean(axis=1).iloc[0])
    print(f"\n  参考: ユニバース全{len(UNIVERSE)}銘柄・等ウェイト保有: "
         f"最終={universe_equal.iloc[-1]:.2f}倍")
    best_lev_final = bs.backtest_concentrated_portfolio(close, selected_symbols, 1.7).iloc[-1]
    verdict = ("Buffett流選定+レバレッジがユニバース平均を上回った"
              if best_lev_final > universe_equal.iloc[-1]
              else "この期間・ユニバースでは、安全性を重視した選定は"
                   "ユニバース平均に見劣りした（強気相場では防御的な銘柄が"
                   "相対的に取り残されやすい）")
    print(f"  → {verdict}")

    print(
        "\n注意: Quality/Valueはライブ断面のみ（先読みバイアスを避けるため"
        "\n過去バックテストには使用していない）。Safety(β)は価格ベースで"
        "\n全期間先読みなく計算可能。両手法とも「現代データへの翻訳」の"
        "\n出発点であり、この検証だけで手法の優劣を断定するものではない。"
    )


if __name__ == "__main__":
    main()
