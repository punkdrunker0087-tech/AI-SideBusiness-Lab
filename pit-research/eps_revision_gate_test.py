"""EPS修正率ファクターの3段階ゲート検証。

AQM-01(Project A)で確立した検証パイプラインを再利用する:
  ①新規性ゲート: 既存2テーマ(マクロ/リスクオン軸・価格テクニカル軸)
    の代表ファクター(FX・Rate・Momentum・LowVol・Liquidity)との相関
  ②単独DSR/PBOゲート: 単独のL/Sバックテストで統計的評価
  ③限界貢献度ゲート: ①②を通過した場合のみ、既存プールに加えた効果を測る

⚠️ J-Quants無料プランのデータ範囲(約2年)に合わせ、Project Aの15年
検証とは異なり2年間のみでの検証になる。サンプルが短いほど偶然の
当たりが出やすいため、DSR/PBOの解釈はより慎重に行う。
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "aqm-strategy"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backtest-framework"))

import factors  # noqa: E402
import fx_factor as fx  # noqa: E402
import panel  # noqa: E402
import rate_factor as rate  # noqa: E402
import stats_eval  # noqa: E402
import strategy  # noqa: E402

import eps_revision_factor as erf


def main():
    print("価格データ構築中（2年・225銘柄、キャッシュ利用）…")
    close, volume = panel.build_panel(range_="2y", use_cache=True)
    print(f"  期間: {close.index[0].date()} 〜 {close.index[-1].date()}  "
         f"銘柄数: {close.shape[1]}\n")

    codes = [t.replace(".T", "") for t in panel.UNIVERSE]
    eps_panel = erf.build_pit_panel(codes, close.index)
    eps_panel.columns = [c + ".T" for c in eps_panel.columns]
    eps_panel = eps_panel.reindex(columns=close.columns)

    coverage = eps_panel.notna().mean(axis=1)
    print(f"EPS修正率パネルの平均カバレッジ（横断で値がある銘柄の割合）: "
         f"{coverage.mean()*100:.1f}%（直近日: {coverage.iloc[-1]*100:.1f}%）\n")

    eps_score = factors.zscore_cross(eps_panel)

    print("=" * 78)
    print("① 新規性ゲート: 既存ファクターとの相関（実現リターン系列）")
    print("=" * 78)
    fx_close = fx.fetch_usdjpy(range_="2y", use_cache=True)
    rate_close = rate.fetch_us10y(range_="2y", use_cache=True)
    zM = factors.zscore_cross(factors.momentum(close))
    zS = factors.zscore_cross(factors.volatility(close))
    zL = factors.zscore_cross(factors.liquidity(close, volume))
    zFX = fx.fx_zscore_factor(close, fx_close, window=252)
    zRate = rate.rate_zscore_factor(close, rate_close, window=126)

    existing = {"Momentum": zM, "LowVol": -zS, "Liquidity": zL, "FX": zFX, "Rate": zRate}
    rets = {}
    for name, score in existing.items():
        res = strategy.backtest(close, score, top_q=0.2, rebalance="ME")
        rets[name] = res.returns
    res_eps = strategy.backtest(close, eps_score, top_q=0.2, rebalance="ME")
    rets["EPS_Revision"] = res_eps.returns

    ret_df = pd.DataFrame(rets)
    corr = ret_df.corr()
    print(corr[["EPS_Revision"]].round(3).to_string())
    max_corr = corr["EPS_Revision"].drop("EPS_Revision").abs().max()
    novelty_pass = max_corr < 0.5
    print(f"\n  既存ファクターとの最大絶対相関: {max_corr:.3f} "
         f"→ {'①合格' if novelty_pass else '①不合格'}（閾値0.5）")

    print("\n" + "=" * 78)
    print("② 単独DSR/PBOゲート: top_q×rebalanceのグリッドサーチ")
    print("=" * 78)
    print(
        "⚠️ EPS修正率には価格ベースのFX/Rateのような「ローリング窓」の"
        "\nパラメータが自然には存在しない（開示イベント駆動のため）。代わりに"
        "\ntop_q(上下何割を選ぶか)×rebalance(頻度)で正真正銘6通りの構成を"
        "\n試す（実装時、同じ設定を3回複製しただけの偽グリッドを組んでしまい"
        "\nDSRを不当に押し上げていたバグを発見・修正した）。"
    )
    grid, ret_series = [], {}
    for top_q in [0.1, 0.2, 0.3]:
        for rebalance in ["ME", "W"]:
            res = strategy.backtest(close, eps_score, top_q=top_q, rebalance=rebalance)
            m = strategy.metrics(res.returns, res.equity)
            key = (top_q, rebalance)
            ret_series[key] = res.returns
            grid.append({"top_q": top_q, "rebalance": rebalance,
                        "total_return": m["total_return"], "sharpe": m["sharpe"]})
    df_grid = pd.DataFrame(grid).sort_values("sharpe", ascending=False)
    print(df_grid.round(3).to_string(index=False))

    common_index = None
    for r in ret_series.values():
        common_index = r.index if common_index is None else common_index.intersection(r.index)
    returns_matrix = np.column_stack(
        [ret_series[k].reindex(common_index).fillna(0.0).values for k in ret_series])
    per_period_sharpes = returns_matrix.mean(axis=0) / returns_matrix.std(axis=0, ddof=1)
    best_idx = int(np.nanargmax(per_period_sharpes))
    best_key = list(ret_series.keys())[best_idx]
    dsr = stats_eval.deflated_sharpe_ratio(returns_matrix[:, best_idx], per_period_sharpes)
    pbo = stats_eval.pbo_cscv(returns_matrix, n_splits=6)
    print(f"\n  最良: {best_key}  DSR={dsr['dsr']:.3f}  PBO={pbo['pbo']:.3f}")
    dsr_pass = dsr["dsr"] > 0.5 and pbo["pbo"] < 0.3
    print(f"  → {'②合格' if dsr_pass else '②不合格'}"
         f"（DSR>0.5かつPBO<0.3の両方を要求。DSR単独では見誤る"
         f"——DSRが基準を満たしてもPBOが高ければ過学習を疑う）")

    if not (novelty_pass and dsr_pass):
        print("\n①または②で不合格のため、③限界貢献度ゲートは実施しない。")
        return

    print("\n" + "=" * 78)
    print("③ 限界貢献度ゲート")
    print("=" * 78)
    combined = (zM + (-zS) + zL + zFX + zRate) / 5.0
    res_without = strategy.backtest(close, combined, top_q=0.2, rebalance="ME")
    combined_with = (zM + (-zS) + zL + zFX + zRate + eps_score) / 6.0
    res_with = strategy.backtest(close, combined_with, top_q=0.2, rebalance="ME")
    m_without = strategy.metrics(res_without.returns, res_without.equity)
    m_with = strategy.metrics(res_with.returns, res_with.equity)
    print(f"  EPS修正率なし: {strategy.format_metrics(m_without)}")
    print(f"  EPS修正率あり: {strategy.format_metrics(m_with)}")


if __name__ == "__main__":
    main()
