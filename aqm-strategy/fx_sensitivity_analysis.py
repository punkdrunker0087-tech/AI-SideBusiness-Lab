"""円安・円高への銘柄ごとの感応度（FXベータ）ファクターの検証。

背景: Momentum/LowVol/Liquidityは価格・出来高の統計パターンのみで、
為替・金利・政策等のマクロ要因を一切考慮しない。ユーザーからの
「為替や政策の時代背景が反映されていないのでは」という指摘を受け、
「銘柄ごとのドル円変化への感応度」を新しいクロスセクショナル・ファクター
として構築し、既存の3ファクターと同じDSR/PBO基準で検証する。

## 検証したこと・分かったこと
1. FXベータ単独（window・rebalanceのグリッドサーチ）: 最良(504日窓・月次)で
   Sharpe+0.371・DSR=0.714・PBO=0.016と、既存3ファクターのグリッドサーチ
   （最良でもDSR=0.247）より明確に良好。
2. 既存3ファクターへFXを混ぜた場合: FXの配分比率を上げるほど単調に改善し、
   **最良は「既存3ファクターを使わずFXのみ」（100%）**という結果になった。
   これは「既存3ファクターが足を引っ張っていた」ことの裏返しでもある。
3. ただし、この混合比率グリッド自体でDSR/PBOを取り直すとDSR=0.442・
   PBO=0.198と、1のグリッドほど強い確信度は出ない（トライアルの
   組み方次第でDSRの見え方が変わる、という多重検定評価自体の難しさ）。
4. **最大の留保**: 検証期間（2011-2026）はドル円が78円→163円まで
   ほぼ一貫して円安方向に動いた「単一のFXスーパーサイクル」であり、
   複数の独立した為替サイクルを経ていない。そのため「FXベータ」が
   本当に構造的なリスクプレミアムなのか、単に「たまたまこの15年
   持続した一方向トレンドに乗れた」だけなのかを、この検証だけでは
   区別できない。円高局面が今後続いた場合に同じ関係が成り立つ保証はない。
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent / "backtest-framework"))
import stats_eval  # noqa: E402

import factors
import fx_factor as fx
import panel
import strategy


def grid_dsr_pbo(ret_series: dict) -> dict:
    common_index = None
    for r in ret_series.values():
        common_index = r.index if common_index is None else common_index.intersection(r.index)
    returns_matrix = np.column_stack(
        [ret_series[k].reindex(common_index).fillna(0.0).values for k in ret_series])
    per_period_sharpes = returns_matrix.mean(axis=0) / returns_matrix.std(axis=0, ddof=1)
    best_idx = int(np.nanargmax(per_period_sharpes))
    best_key = list(ret_series.keys())[best_idx]
    best_returns = returns_matrix[:, best_idx]
    dsr = stats_eval.deflated_sharpe_ratio(best_returns, per_period_sharpes)
    pbo = stats_eval.pbo_cscv(returns_matrix, n_splits=10)
    return {"best_key": best_key, "dsr": dsr, "pbo": pbo}


def main():
    print("パネル構築中（15年・225銘柄・キャッシュ利用）…")
    close, volume = panel.build_panel(range_="15y", use_cache=True)
    fx_close = fx.fetch_usdjpy(range_="15y", use_cache=True)
    print(f"  USD/JPY 期間: {fx_close.index[0].date()}〜{fx_close.index[-1].date()}"
         f"  ({fx_close.iloc[0]:.1f}円 → {fx_close.iloc[-1]:.1f}円)\n")

    print("=" * 78)
    print("① FXベータ単独のグリッドサーチ（window×rebalance）")
    print("=" * 78)
    grid1, ret1 = [], {}
    for window in [126, 252, 504]:
        for rebalance in ["ME", "W"]:
            score = fx.fx_zscore_factor(close, fx_close, window=window)
            res = strategy.backtest(close, score, top_q=0.2, rebalance=rebalance)
            m = strategy.metrics(res.returns, res.equity)
            ret1[(window, rebalance)] = res.returns
            grid1.append({"window": window, "rebalance": rebalance,
                         "total_return": m["total_return"], "sharpe": m["sharpe"]})
    df1 = pd.DataFrame(grid1).sort_values("sharpe", ascending=False)
    print(df1.round(3).to_string(index=False))
    r1 = grid_dsr_pbo(ret1)
    print(f"\n  最良: {r1['best_key']}  DSR={r1['dsr']['dsr']:.3f}  PBO={r1['pbo']['pbo']:.3f}")

    print("\n" + "=" * 78)
    print("② 既存3ファクター(M+σ+L)へFX(504日窓)を混ぜた場合の配分比率感度")
    print("=" * 78)
    zM = factors.zscore_cross(factors.momentum(close))
    zS = factors.zscore_cross(factors.volatility(close))
    zL = factors.zscore_cross(factors.liquidity(close, volume))
    zFX = fx.fx_zscore_factor(close, fx_close, window=504)

    grid2, ret2 = [], {}
    for fx_share in [0.0, 0.25, 0.50, 0.75, 0.90, 1.0]:
        if fx_share >= 1.0:
            score = zFX
        else:
            raw = {"M": 0.40, "sigma": -0.20, "L": 0.15,
                  "FX": fx_share / (1 - fx_share) * 0.75}
            abs_sum = sum(abs(v) for v in raw.values())
            w = {k: v / abs_sum for k, v in raw.items()}
            score = w["M"] * zM + w["sigma"] * zS + w["L"] * zL + w["FX"] * zFX
        res = strategy.backtest(close, score, top_q=0.2, rebalance="ME")
        m = strategy.metrics(res.returns, res.equity)
        ret2[fx_share] = res.returns
        grid2.append({"FX_share": fx_share, "total_return": m["total_return"],
                     "sharpe": m["sharpe"], "max_dd": m["max_drawdown"]})
    df2 = pd.DataFrame(grid2)
    print(df2.round(3).to_string(index=False))
    r2 = grid_dsr_pbo(ret2)
    print(f"\n  最良FX_share: {r2['best_key']}  DSR={r2['dsr']['dsr']:.3f}  "
         f"PBO={r2['pbo']['pbo']:.3f}")

    print("\n" + "=" * 78)
    print("結論（誠実な報告）")
    print("=" * 78)
    print(
        "・FXベータ単独は既存3ファクター単独より明確に良い(①のDSR/PBOが良好)\n"
        "・既存3ファクターへ混ぜると、FX比率を上げるほど単調に改善し、最良は\n"
        "  「既存3ファクターを使わずFXのみ」という結果だった（既存3ファクター\n"
        "  が足を引っ張っていたことの裏返し）\n"
        "・ただし混合比率グリッドでDSR/PBOを取り直すと①より確信度は下がる\n"
        "  （どの試行集合と比較するかでDSRの値そのものが変わる、という\n"
        "  多重検定評価自体の難しさを示す結果でもある）\n"
        "・最大の留保: 検証期間はドル円が一貫して円安方向に動いた単一の\n"
        "  スーパーサイクルであり、複数の独立した為替サイクルを経ていない。\n"
        "  「本物の構造的なリスクプレミアム」なのか「たまたま一方向トレンドに\n"
        "  乗れただけ」なのかは、この検証だけでは判別できない"
    )


if __name__ == "__main__":
    main()
