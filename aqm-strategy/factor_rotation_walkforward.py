"""ループ学習的なファクター運用 ―― 各時点までのデータだけで直近成績を
評価し、ファクター配分比率を毎期更新しながらウォークフォワードで検証する。

ユーザー提案「FXベータをループ学習する分析ファクターの一つとして
活用すれば良い」を実装したもの。これまでのAQM-01は固定重み
（M=0.40, σ=-0.20, L=0.15、あるいはFXを固定比率で追加）だったが、
ここでは「その時点で直近有効だったファクターを重視し、効いていない
ファクターの配分は下げる」という動的な設計にする。

## 方法（先読み防止の設計）
1. 候補ファクター群 {Momentum, LowVol, Liquidity, FX} を定義する。
   各ファクターは単独のロング/ショート・スコアとして、符号を「高いほど
   良い」に統一する（LowVolは-zσ、他はそのまま）。
2. 各ファクターの単独バックテスト日次リターン（全期間、Zスコア自体は
   ローリング計算で先読みなし）を事前に計算しておく。
3. 年次の評価日tにおいて、**tより前のデータのみ**を使い、各ファクターの
   直近lookback日間の実現Sharpeを計算する。
4. 直近Sharpeがプラスのファクターだけを、そのSharpeに比例した重みで
   組み合わせる（全てマイナスならその期間はノーポジション＝現金）。
   この重みは次の評価日まで固定する（tだけで決まり、t以降のデータは
   一切参照しないので先読みではない）。
5. これを15年間、年次で繰り返し、最終的な複合スコアでL/Sバックテストする。

固定配分（既存3ファクター固定・FX固定混合）と比較し、動的化が
実際に改善するかを検証する。
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


def build_factor_scores(close: pd.DataFrame, volume: pd.DataFrame,
                        fx_close: pd.Series, fx_window: int = 504) -> dict:
    """各ファクターの単独スコア（符号統一済み、高いほど良い）を返す。"""
    zM = factors.zscore_cross(factors.momentum(close))
    zS = factors.zscore_cross(factors.volatility(close))
    zL = factors.zscore_cross(factors.liquidity(close, volume))
    zFX = fx.fx_zscore_factor(close, fx_close, window=fx_window)
    return {"Momentum": zM, "LowVol": -zS, "Liquidity": zL, "FX": zFX}


def factor_standalone_returns(close: pd.DataFrame, scores: dict,
                              top_q: float = 0.2, rebalance: str = "ME") -> pd.DataFrame:
    """各ファクター単独でのL/S日次リターン（全期間、比較・評価用）。"""
    rets = {}
    for name, score in scores.items():
        res = strategy.backtest(close, score, top_q=top_q, rebalance=rebalance)
        rets[name] = res.returns
    return pd.DataFrame(rets)


def annual_eval_dates(index: pd.DatetimeIndex) -> list:
    s = pd.Series(index, index=index)
    return s.resample("YE").last().dropna().tolist()


def walk_forward_factor_rotation(close: pd.DataFrame, scores: dict,
                                 standalone_returns: pd.DataFrame,
                                 lookback: int = 504) -> dict:
    """年次で直近Sharpeに応じてファクター重みを更新するウォークフォワード。

    各評価日tでは standalone_returns.loc[:t] の末尾lookback日だけを使い、
    そこで決めた重みは**tより後、次の評価日まで**の期間に適用する
    （実装時、tまでのデータで決めた重みをtで終わる同じ期間に適用して
    しまう先読みバグがあり、その年自身のリターンが重み決定に混入して
    いた。評価日の翌日から次の評価日までへ適用するよう修正した）。
    """
    eval_dates = annual_eval_dates(close.index)
    factor_names = list(scores.keys())
    weight_history = {}

    blended = pd.DataFrame(0.0, index=close.index, columns=close.columns)

    # 最初の評価日までのウォームアップ期間は等配分
    warmup_mask = close.index <= eval_dates[0]
    eq_w = 1.0 / len(factor_names)
    for n in factor_names:
        blended.loc[warmup_mask] = blended.loc[warmup_mask].add(
            scores[n].loc[warmup_mask] * eq_w, fill_value=0.0)

    for i, t in enumerate(eval_dates):
        trailing = standalone_returns.loc[:t].iloc[-lookback:]
        if len(trailing) < lookback // 2:
            w = {n: 1.0 / len(factor_names) for n in factor_names}  # データ不足期間は等配分
        else:
            sharpes = {n: trailing[n].mean() / trailing[n].std() if trailing[n].std() else 0.0
                      for n in factor_names}
            positive = {n: max(s, 0.0) for n, s in sharpes.items()}
            total = sum(positive.values())
            if total > 0:
                w = {n: v / total for n, v in positive.items()}
            else:
                # 全てマイナス→「現金化」を意図したが、複合スコアが全銘柄で
                # 同一値(0)になるとstrategy.backtestのnlargest/nsmallestが
                # 同点の中から任意選択してしまい、実質ランダムなポジションを
                # 取ってしまうバグがあった（strategy.backtestはクロス
                # セクショナル・ランキング方式のため「ノーポジション」を
                # 表現できない）。代わりに等配分にフォールバックする。
                w = {n: 1.0 / len(factor_names) for n in factor_names}
        weight_history[t] = w

        # tで決めた重みは、tの"次"から次の評価日までに適用する
        next_t = eval_dates[i + 1] if i + 1 < len(eval_dates) else close.index[-1]
        period_mask = (close.index > t) & (close.index <= next_t)
        for n in factor_names:
            blended.loc[period_mask] = blended.loc[period_mask].add(
                scores[n].loc[period_mask] * w[n], fill_value=0.0)

    return {"blended_score": blended, "weight_history": weight_history}


def main():
    print("パネル構築中（15年・225銘柄・キャッシュ利用）…")
    close, volume = panel.build_panel(range_="15y", use_cache=True)
    fx_close = fx.fetch_usdjpy(range_="15y", use_cache=True)

    scores = build_factor_scores(close, volume, fx_close)
    standalone = factor_standalone_returns(close, scores)

    print("\n各ファクター単独の全期間成績（参考）:")
    for name in scores:
        m = strategy.metrics(standalone[name], (1 + standalone[name]).cumprod())
        print(f"  {name:10s}: {strategy.format_metrics(m)}")

    wf = walk_forward_factor_rotation(close, scores, standalone, lookback=504)
    print("\n年次のファクター配分比率（直近504日の実現Sharpeに基づく、先読みなし）:")
    for t, w in wf["weight_history"].items():
        w_str = "  ".join(f"{n}={v:.2f}" for n, v in w.items())
        print(f"  {t.date()}: {w_str}")

    res_wf = strategy.backtest(close, wf["blended_score"], top_q=0.2, rebalance="ME")
    m_wf = strategy.metrics(res_wf.returns, res_wf.equity)
    print(f"\n【ループ学習型（年次動的配分）】 {strategy.format_metrics(m_wf)}")

    # 比較: 固定3ファクター・固定FXのみ・固定50/50混合
    fixed_3f = strategy.WEIGHTS["M"] * scores["Momentum"] + \
              strategy.WEIGHTS["sigma"] * (-scores["LowVol"]) + \
              strategy.WEIGHTS["L"] * scores["Liquidity"]
    res_3f = strategy.backtest(close, fixed_3f, top_q=0.2, rebalance="ME")
    m_3f = strategy.metrics(res_3f.returns, res_3f.equity)
    print(f"【固定3ファクターのみ】       {strategy.format_metrics(m_3f)}")

    res_fx = strategy.backtest(close, scores["FX"], top_q=0.2, rebalance="ME")
    m_fx = strategy.metrics(res_fx.returns, res_fx.equity)
    print(f"【固定FXのみ】               {strategy.format_metrics(m_fx)}")

    universe_eq = (close.mean(axis=1) / close.mean(axis=1).iloc[0])
    print(f"\n参考: ユニバース全{len(close.columns)}銘柄・均等保有 最終={universe_eq.iloc[-1]:.2f}倍")

    print("\n年次リターン比較:")
    y_wf = res_wf.returns.groupby(res_wf.returns.index.year).apply(lambda r: (1 + r).prod() - 1)
    y_3f = res_3f.returns.groupby(res_3f.returns.index.year).apply(lambda r: (1 + r).prod() - 1)
    y_fx = res_fx.returns.groupby(res_fx.returns.index.year).apply(lambda r: (1 + r).prod() - 1)
    for y in y_wf.index:
        print(f"  {y}: ループ学習 {y_wf[y]*100:+6.1f}%   固定3F {y_3f.get(y, float('nan'))*100:+6.1f}%"
             f"   固定FX {y_fx.get(y, float('nan'))*100:+6.1f}%")

    # DSR/PBO: ループ学習 vs 固定3F vs 固定FX vs 固定50/50 の4通りを比較
    fixed_5050 = fixed_3f * 0.5 + scores["FX"] * 0.5
    res_5050 = strategy.backtest(close, fixed_5050, top_q=0.2, rebalance="ME")

    ret_series = {"loop_learning": res_wf.returns, "fixed_3factor": res_3f.returns,
                 "fixed_fx_only": res_fx.returns, "fixed_50_50": res_5050.returns}
    common_index = None
    for r in ret_series.values():
        common_index = r.index if common_index is None else common_index.intersection(r.index)
    returns_matrix = np.column_stack(
        [ret_series[k].reindex(common_index).fillna(0.0).values for k in ret_series])
    per_period_sharpes = returns_matrix.mean(axis=0) / returns_matrix.std(axis=0, ddof=1)
    best_idx = int(np.nanargmax(per_period_sharpes))
    best_key = list(ret_series.keys())[best_idx]
    dsr = stats_eval.deflated_sharpe_ratio(returns_matrix[:, best_idx], per_period_sharpes)
    pbo = stats_eval.pbo_cscv(returns_matrix, n_splits=10)
    print(f"\nDSR/PBO比較（ループ学習 vs 固定3F vs 固定FX vs 固定50/50、4通り）:")
    print(f"  最良: {best_key}  DSR={dsr['dsr']:.3f}  PBO={pbo['pbo']:.3f}")


if __name__ == "__main__":
    main()
