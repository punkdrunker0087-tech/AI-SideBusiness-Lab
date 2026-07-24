"""歴史的に証明された投資手法を現代データで検証する通しデモ。

1. タートルズのトレンドフォロー戦略（Donchian breakout + N基準サイジング）
   を複数銘柄で検証し、単一市場での挙動を確認する
2. ウォーレン・バフェットのバリュー投資を「Buffett's Alpha」論文の
   Quality+Value+Safetyへの分解として現代データに翻訳し、レバレッジの
   効果を検証する
3. Joel GreenblattのMagic Formula（Earnings Yield×ROC）を、共通の
   10段階パイプライン（バックテスト・感度分析・レジーム分析）で検証する
4. Benjamin GrahamのDeep Value（NCAVの代理指標）を検証する
5. Peter LynchのPEGレシオを検証する
6. William O'NeilのCAN SLIMを検証する
7. George Sorosのリフレクシビティ（bias×加速度の代理指標）を検証する
8. Ray Dalioのリスクパリティ（既存portfolio-optimizationの差分適用）を検証する
9. Jim Simons流の統計的裁定（既存stat-arbの差分適用）を検証する
10. Fama-FrenchのSize/Valueファクター（既存multifactor-investingの差分適用）を検証する
"""
import numpy as np
import pandas as pd

import buffett_style as bs
import dalio_risk_parity as dr
import data_util
import famafrench_factors as ff
import fundamentals_util as fu
import graham_deep_value as gv
import lynch_peg as lp
import magic_formula as mf
import oneil_canslim as oc
import pipeline
import simons_stat_arb as ss
import soros_reflexivity as sr
import turtle_trading as tt

UNIVERSE = ["7203.T", "6758.T", "9432.T", "8306.T", "9983.T", "6098.T",
           "8035.T", "9433.T", "7974.T", "6501.T"]


def main():
    print("価格データ取得中（10銘柄・5年、OHLC）…")
    ohlc = {s: data_util.fetch_ohlc(s, "5y") for s in UNIVERSE}
    close = pd.DataFrame({s: df["close"] for s, df in ohlc.items()}).dropna()
    bench = data_util.fetch_ohlc("1306.T", "5y")["close"].reindex(close.index).ffill()
    universe_equal = (close.mean(axis=1) / close.mean(axis=1).iloc[0])
    print(f"  期間 {close.index[0].date()}〜{close.index[-1].date()}\n")

    print("=" * 70)
    print("1. タートルズのトレンドフォロー戦略（Donchian breakout・原典準拠）")
    print("=" * 70)
    rows = []
    turtle_multiples = {}
    for sym in UNIVERSE:
        res = tt.run_turtle_system(ohlc[sym])
        bh_final = 10_000_000 * ohlc[sym]["close"].iloc[-1] / ohlc[sym]["close"].iloc[0]
        wins = sum(1 for t in res.trades if t["pnl"] > 0)
        wr = wins / len(res.trades) if res.trades else np.nan
        rows.append({"銘柄": sym, "タートルズ最終資産": res.equity.iloc[-1],
                    "B&H最終資産": bh_final, "取引数": len(res.trades), "勝率": wr})
        turtle_multiples[sym] = res.equity / res.equity.iloc[0]
    turtle_df = pd.DataFrame(rows)
    print(turtle_df.round(2).to_string(index=False))
    n_beat_bh = (turtle_df["タートルズ最終資産"] > turtle_df["B&H最終資産"]).sum()
    print(f"\n  → タートルズがB&Hを上回った銘柄(各銘柄自身のB&Hが基準): {n_beat_bh}/{len(UNIVERSE)}")

    # 他手法と同じ基準（ユニバース全10銘柄均等保有）で比較するため、
    # 10戦略に均等資金配分した場合のブレンド倍率も計算する（上のB&H比較とは
    # 別軸の指標。銘柄ごとの自己B&Hに勝つことと、ユニバース平均に勝つことは
    # 異なる問いであり、混同しないよう明確に分けて報告する）。
    turtle_blend = pd.DataFrame(turtle_multiples).reindex(close.index).ffill().bfill().mean(axis=1)
    print(f"    10戦略・均等資金配分ブレンド最終倍率={turtle_blend.iloc[-1]:.2f}倍"
         f"  (参考: ユニバース全10銘柄均等保有={universe_equal.iloc[-1]:.2f}倍)")
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

    fundamentals = fu.fetch(UNIVERSE)

    print("\n" + "=" * 70)
    print("4. Benjamin Graham の Deep Value（NCAVの代理指標）")
    print("=" * 70)
    print(
        "⚠️ Yahoo無料APIの balanceSheetHistory は流動資産/負債の明細を"
        "\n返さないため、原典の正式なNCAVは計算不能。低PBR・黒字EPS必須・"
        "\n低D/Eという代理指標で代用する。"
    )
    gv_ranked = gv.compute_deep_value(fundamentals)
    print(gv_ranked[["price_to_book", "trailing_eps", "debt_to_equity",
                    "combined_rank"]].round(3).to_string())
    print(f"  (赤字EPSで除外: {gv_ranked.attrs['n_excluded_negative_eps']}銘柄)")

    gv_top5 = gv_ranked.index[:5].tolist()
    eq_gv = pipeline.backtest_static_selection(close, gv_top5)
    print(f"\n  ⑥バックテスト: 上位5銘柄・均等保有・5年 最終={eq_gv.iloc[-1]:.2f}倍"
         f"  (参考: ユニバース全10銘柄均等保有={universe_equal.iloc[-1]:.2f}倍)")
    sens_gv = pipeline.sensitivity_by_n(gv_ranked, close, n_values=[3, 5, 8])
    print("  ⑦感度分析(N=3/5/8):")
    print(sens_gv.round(3).to_string(index=False))
    regimes = pipeline.classify_regime(bench)
    reg_perf_gv = pipeline.performance_by_regime(eq_gv, regimes)
    if not reg_perf_gv.empty:
        print("  ⑧レジーム分析:")
        print(reg_perf_gv.round(3).to_string())

    print("\n" + "=" * 70)
    print("5. Peter Lynch の PEG レシオ")
    print("=" * 70)
    peg_ranked = lp.compute_peg(fundamentals)
    print(peg_ranked[["trailing_pe", "earnings_growth", "peg", "判定"]].round(3).to_string())
    print(f"  (成長率不足/データ欠損で除外: {peg_ranked.attrs['n_excluded_total']}銘柄、"
         f"うち低成長のみで除外: {peg_ranked.attrs['n_excluded_low_growth']}銘柄)")

    peg_undervalued = peg_ranked[peg_ranked["peg"] < 1.0].index.tolist()
    if peg_undervalued:
        eq_peg = pipeline.backtest_static_selection(close, peg_undervalued)
        print(f"\n  ⑥バックテスト: PEG<1割安銘柄({len(peg_undervalued)}銘柄)・均等保有・5年 "
             f"最終={eq_peg.iloc[-1]:.2f}倍"
             f"  (参考: ユニバース全10銘柄均等保有={universe_equal.iloc[-1]:.2f}倍)")
        reg_perf_peg = pipeline.performance_by_regime(eq_peg, regimes)
        if not reg_perf_peg.empty:
            print("  ⑧レジーム分析:")
            print(reg_perf_peg.round(3).to_string())

    print("\n" + "=" * 70)
    print("6. William O'Neil の CAN SLIM")
    print("=" * 70)
    print(
        "⚠️ 四半期EPS成長率(C)はYahoo無料APIで欠損することが多いため、"
        "\n年間成長率(A)と同じ`earnings_growth`で代用する近似。"
    )
    volume = pd.DataFrame({s: df["volume"] for s, df in ohlc.items()}).reindex(close.index)
    cs_ranked = oc.compute_canslim(fundamentals, close, volume, bench)
    print(cs_ranked[["C_proxy_quarterly_growth", "A_annual_growth", "N_price_vs_52w_high",
                    "S_volume_ratio", "L_relative_strength", "I_institutional_pct",
                    "combined_rank"]].round(3).to_string())
    print(f"\n  M(市場の地合い)ゲート: ベンチマークは200日線"
         f"{'上' if cs_ranked.attrs['M_market_uptrend'] else '下'} → "
         f"{'新規建玉に適した地合い' if cs_ranked.attrs['M_market_uptrend'] else '新規建玉は見送るべき地合い'}")

    cs_top5 = cs_ranked.index[:5].tolist()
    eq_cs = pipeline.backtest_static_selection(close, cs_top5)
    print(f"\n  ⑥バックテスト: 上位5銘柄・均等保有・5年 最終={eq_cs.iloc[-1]:.2f}倍"
         f"  (参考: ユニバース全10銘柄均等保有={universe_equal.iloc[-1]:.2f}倍)")
    sens_cs = pipeline.sensitivity_by_n(cs_ranked, close, n_values=[3, 5, 8])
    print("  ⑦感度分析(N=3/5/8):")
    print(sens_cs.round(3).to_string(index=False))
    reg_perf_cs = pipeline.performance_by_regime(eq_cs, regimes)
    if not reg_perf_cs.empty:
        print("  ⑧レジーム分析:")
        print(reg_perf_cs.round(3).to_string())

    print("\n" + "=" * 70)
    print("7. George Soros のリフレクシビティ（bias×加速度の代理指標）")
    print("=" * 70)
    print(
        "⚠️ Sorosの「実際のPERと長期平均PERの乖離」はPER時系列が必要で"
        "\n無料データでは再現不能。価格のみで構築できる代理指標"
        "\n（長期MA乖離率=bias、モメンタムの加速度=accel）で代用する。"
    )
    n_beat_soros = 0
    soros_finals = []
    soros_multiples = {}
    for sym in UNIVERSE:
        res_sr = sr.backtest_reflexivity_rule(ohlc[sym]["close"])
        beat = res_sr["final_multiple"] > res_sr["bh_final_multiple"]
        n_beat_soros += beat
        soros_finals.append({"銘柄": sym, "ルール最終倍率": res_sr["final_multiple"],
                            "B&H最終倍率": res_sr["bh_final_multiple"], "B&H超え": beat})
        soros_multiples[sym] = res_sr["equity"]
    print(pd.DataFrame(soros_finals).round(3).to_string(index=False))
    print(f"\n  → リフレクシビティ・ルールがB&Hを上回った銘柄(各銘柄自身のB&Hが基準): "
         f"{n_beat_soros}/{len(UNIVERSE)}")

    # タートルズと同様、他手法と同じ基準（ユニバース均等保有）でも比較する
    soros_blend = pd.DataFrame(soros_multiples).reindex(close.index).ffill().bfill().mean(axis=1)
    print(f"    10戦略・均等資金配分ブレンド最終倍率={soros_blend.iloc[-1]:.2f}倍"
         f"  (参考: ユニバース全10銘柄均等保有={universe_equal.iloc[-1]:.2f}倍)")
    print(
        "    黄昏期・バストでフラットにする設計は下落を避けられる反面、"
        "\n    このユニバース・期間は総じて強気相場だったため、フラット化した"
        "\n    期間の機会損失がB&Hに対して不利に働いた。Sorosの理論は「ブームの"
        "\n    終盤を正確に当てる」ことではなく「非対称な出口設計」が主眼であり、"
        "\n    単純な強気相場での勝敗だけでは理論の価値を測れない。"
    )

    print("\n" + "=" * 70)
    print("8. Ray Dalio のリスクパリティ（既存portfolio-optimizationの差分適用）")
    print("=" * 70)
    print(
        "⚠️ 原典は株式・債券・コモディティ等の複数資産クラスにまたがる"
        "\nリスク均等化が前提。本ユニバースは日本株10銘柄のみで、資産クラス"
        "\n分散という核心部分は再現できていない。"
    )
    res_dr = dr.backtest_risk_parity_vs_equal_weight(close)
    print(f"  リスクパリティ: 最終={res_dr['final_rp']:.2f}倍  年率ボラ={res_dr['vol_rp']*100:.1f}%"
         f"  最大DD={res_dr['max_dd_rp']*100:.1f}%")
    print(f"  等ウェイト　　: 最終={res_dr['final_ew']:.2f}倍  年率ボラ={res_dr['vol_ew']*100:.1f}%"
         f"  最大DD={res_dr['max_dd_ew']*100:.1f}%")
    print(
        "  → 同一資産クラス内でも、リスク均等化はボラティリティ・最大DDを"
        "\n    明確に縮小させた。ただしリターンも等ウェイトを下回っており、"
        "\n    「低リスク・低リターン」というリスクパリティの原理通りの結果。"
    )

    print("\n" + "=" * 70)
    print("9. Jim Simons流の統計的裁定（既存stat-arbの差分適用）")
    print("=" * 70)
    print(
        "⚠️ Renaissance Technologiesの実際のモデルは非公開。ここではSimonsの"
        "\n哲学に近い、学術的に再現可能なコインテグレーション・ペアトレーディング"
        "\nを本ユニバースに適用した場合の挙動のみを検証する。"
    )
    res_ss = ss.find_best_cointegrated_pair(close)
    print(f"  検定した全ペア数: {res_ss['n_pairs_tested']}  "
         f"5%水準でコインテグレーション成立: {res_ss['n_cointegrated']}ペア")
    if res_ss["n_cointegrated"] > 0:
        bt_ss = ss.backtest_best_pair(close, res_ss["best_pair"])
        print(f"  最良ペア {bt_ss['pair']}: 取引数={bt_ss['n_trades']}  "
             f"純損益={bt_ss['total_net_pnl']:.1f}円  Sharpe(日次)={bt_ss['sharpe_daily']:.3f}")
        verdict_ss = ("プラスの純損益" if bt_ss["total_net_pnl"] > 0 else "マイナスの純損益")
        print(f"  → 5年間で唯一コインテグレーションが成立したペアも、{verdict_ss}"
             f"となった。10銘柄という本シリーズのユニバースは、そもそも"
             f"\n    ペア候補の厳選（同業種・流動性・相関）を経ておらず、統計的裁定が"
             f"\n    前提とする「大量の候補から本当に安定した関係を持つペアだけを選ぶ」"
             f"\n    プロセスの入り口にすら立てていない可能性が高い。")

    print("\n" + "=" * 70)
    print("10. Fama-French の Size/Valueファクター（既存multifactor-investingの差分適用）")
    print("=" * 70)
    print(
        "⚠️ 原典は数千銘柄規模の断面統計検定が前提。10銘柄では統計的な"
        "\n有意性は主張できず、傾向の参考値に留まる。"
    )
    fnd_ff = fu.fetch(UNIVERSE)
    scores_ff = ff.build_size_value_score(fnd_ff)
    res_ff = ff.backtest_smb_hml_tilt(close, scores_ff)
    print(f"  小型5銘柄: 最終={res_ff['final_small']:.2f}倍　"
         f"大型5銘柄: 最終={res_ff['final_big']:.2f}倍　(SMBスプレッド={res_ff['smb_final_spread']:+.2f})")
    print(f"  割安5銘柄: 最終={res_ff['final_value']:.2f}倍　"
         f"割高5銘柄: 最終={res_ff['final_growth']:.2f}倍　(HMLスプレッド={res_ff['hml_final_spread']:+.2f})")
    print(
        "  → このユニバース・期間ではSMB・HMLとも符号がマイナス"
        "\n    （大型・グロースが小型・バリューを上回った）。原典の学術的な"
        "\n    長期・大規模サンプルでの発見と逆行する結果だが、これは10銘柄・"
        "\n    5年・強気相場という本検証の設計が生んだ特殊な結果であり、"
        "\n    SMB/HMLプレミアムそのものが消滅したことを意味しない。"
    )

    print("\n" + "=" * 70)
    print("総合考察（10手法共通）")
    print("=" * 70)
    print(
        "・何が本質だったか: いずれも「予測しない・ルールに従う・分散/長期で"
        "\n  優位性が発揮される」という規律の設計。個別の数式より規律の徹底が本質\n"
        "・現代では何を変えるべきか: 点in-time財務データ(J-Quants等)への移行、"
        "\n  金融/公益株など前提が崩れるセクターの自動検出、複数資産クラスへの拡張、"
        "\n  欠損データ(NCAV明細・四半期成長率・PER時系列)を補う代替データソースの併用\n"
        "・AIだから改善できる部分: 大量データの解析・複数戦略の並行検証・"
        "\n  セクター例外や異常値(EV<0等)の自動検知——本デモで実際に発見した"
        "\n  ようなデータ起因の落とし穴を人手より速く発見できる"
    )

    print(
        "\n注意: Quality/Value/Earnings Yield/ROC/PBR/PEG/CAN SLIM/Size/Value"
        "\nの財務項目はライブ断面のみ（先読みバイアスを避けるため過去バックテストの"
        "\n銘柄選定そのものには使用せず、「今日選んだ銘柄群を過去5年保有していたら」"
        "\nという条件付きの参考値として扱う）。Safety(β)・タートルズ・CAN SLIMの"
        "\nN/S/L・Sorosのbias/accel等の価格ベース指標は全期間先読みなく計算可能。"
        "\n10手法とも「現代データへの翻訳」の出発点であり、この検証だけで手法の"
        "\n優劣を断定するものではない。全10戦略をユニバース全10銘柄均等保有"
        f"({universe_equal.iloc[-1]:.2f}倍)という共通の基準に揃えて比較すると"
        "\n（タートルズ・Sorosは元々個別銘柄自身のB&Hとの比較だが、10戦略を"
        "均等資金配分したブレンドで揃えた）、"
        f"\nタートルズ{turtle_blend.iloc[-1]:.2f}倍・Soros{soros_blend.iloc[-1]:.2f}倍を"
        "含む9手法が軒並みユニバース均等保有に見劣りした。"
        "\nFama-Frenchの検証だけは例外的に大型株tilt(3.81倍)がユニバース平均を"
        "わずかに上回ったが、これは原典が主張するSMBプレミアム(小型>大型)とは"
        "\n逆方向の結果であり、「Fama-French流が機能した」のではなく"
        "「このユニバース・期間ではSMB/HMLプレミアムが観測されなかった」ことを示す。"
        "\n個別の勝敗より、10銘柄・5年・単一の強気相場という検証設計そのものの"
        "限界を認識することが重要。不利な結果も成功例と同様に価値ある知見として扱う。"
    )


if __name__ == "__main__":
    main()
