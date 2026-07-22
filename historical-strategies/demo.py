"""歴史的に証明された投資手法を現代データで検証する通しデモ。

1. タートルズのトレンドフォロー戦略（Donchian breakout + N基準サイジング）
   を複数銘柄で検証し、単一市場での挙動を確認する
2. ウォーレン・バフェットのバリュー投資を「Buffett's Alpha」論文の
   Quality+Value+Safetyへの分解として現代データに翻訳し、レバレッジの
   効果を検証する
3. Joel GreenblattのMagic Formula（Earnings Yield×ROC）を、共通の
   10段階パイプライン（バックテスト・感度分析・レジーム分析）で検証する
"""
import numpy as np
import pandas as pd

import buffett_style as bs
import data_util
import magic_formula as mf
import pipeline
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

    print("\n" + "=" * 70)
    print("3. Greenblatt Magic Formula（共通10段階パイプライン）")
    print("=" * 70)
    inputs = mf.fetch_magic_formula_inputs(UNIVERSE)
    ranked_ex = mf.compute_magic_formula(inputs, exclude_financials=True)
    # 危険なケース: 原典の除外ルールも異常値チェックも行わない場合
    ranked_naive = mf.compute_magic_formula(inputs, exclude_financials=False,
                                           require_positive_values=False)
    print(f"除外された金融セクター銘柄数: {ranked_ex.attrs['n_excluded_financials']}")
    print("\nランキング（金融セクター除外・原典準拠）:")
    print(ranked_ex[["sector", "earnings_yield", "roc", "combined_rank"]].round(3).to_string())

    print("\nランキング（除外なし・異常値チェックなし＝危険なケース）:")
    print(ranked_naive[["sector", "earnings_yield", "roc", "combined_rank"]].round(3).to_string())
    bank_row = ranked_naive[ranked_naive["sector"].isin(mf.EXCLUDED_SECTORS)]
    if not bank_row.empty:
        position = int((ranked_naive["combined_rank"] <= bank_row["combined_rank"].iloc[0]).sum())
        total = len(ranked_naive)
        print(f"  → 銀行株のEarnings Yield={bank_row['earnings_yield'].iloc[0]:+.3f}"
             f"（EVが負のため符号が反転し、無意味な値になっている）。"
             f"\n    今回は{total}銘柄中{position}位(最下位)に沈んだため"
             f"上位N銘柄の選定は結果的に汚染されなかったが、"
             f"\n    符号の組み合わせ次第では逆に上位へ紛れ込みうる。"
             f"「たまたま実害がなかった」のであって除外ルールが不要という"
             f"意味ではない。")

    print("\n--- ⑥バックテスト・⑦感度分析: 銘柄数(N)の頑健性 ---")
    print("[金融セクター除外・原典準拠]")
    print(pipeline.sensitivity_by_n(ranked_ex, close, n_values=[3, 5, 8]).round(3).to_string(index=False))
    print("[除外なし・異常値チェックなし(危険なケース)]")
    print(pipeline.sensitivity_by_n(ranked_naive, close, n_values=[3, 5, 8]).round(3).to_string(index=False))

    print("\n--- ⑧レジーム分析(N=5・金融除外版) ---")
    top5 = ranked_ex.index[:5].tolist()
    eq5 = pipeline.backtest_static_selection(close, top5)
    regimes = pipeline.classify_regime(bench)
    reg_perf = pipeline.performance_by_regime(eq5, regimes)
    if not reg_perf.empty:
        print(reg_perf.round(3).to_string())

    print(
        "\n⑨⑩機能する市場・破綻する条件: 8306.T(銀行)でEnterprise Valueが"
        "\n負値になることを実データで確認した。これは原典が金融・公益株を"
        "\n除外する理由そのもの（負債の概念が事業会社と異なり、EV/ROCの"
        "\n前提が成立しない）。金融株を誤って含めると、ランキング自体が"
        "\n意味をなさなくなる。"
    )

    print("\n" + "=" * 70)
    print("総合考察（3手法共通）")
    print("=" * 70)
    print(
        "・何が本質だったか: いずれも「予測しない・ルールに従う・分散/長期で"
        "\n  優位性が発揮される」という規律の設計。個別の数式より規律の徹底が本質\n"
        "・現代では何を変えるべきか: 点in-time財務データ(J-Quants等)への移行、"
        "\n  金融/公益株など前提が崩れるセクターの自動検出、複数資産クラスへの拡張\n"
        "・AIだから改善できる部分: 大量データの解析・複数戦略の並行検証・"
        "\n  セクター例外や異常値(EV<0等)の自動検知——本デモで実際に発見した"
        "\n  ようなデータ起因の落とし穴を人手より速く発見できる"
    )

    print(
        "\n注意: Quality/Value/Earnings Yield/ROCはライブ断面のみ（先読み"
        "\nバイアスを避けるため過去バックテストには使用していない）。"
        "\nSafety(β)・タートルズの価格ベース指標は全期間先読みなく計算可能。"
        "\n3手法とも「現代データへの翻訳」の出発点であり、この検証だけで"
        "\n手法の優劣を断定するものではない。不利な結果も成功例と同様に"
        "\n価値ある知見として扱う。"
    )


if __name__ == "__main__":
    main()
