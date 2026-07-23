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


def _sharpe_chasing_weights(trailing: pd.DataFrame, factor_names: list) -> dict:
    """v1: 直近Sharpeがプラスのファクターだけに比例配分する（チェイシング型）。"""
    sharpes = {n: trailing[n].mean() / trailing[n].std() if trailing[n].std() else 0.0
              for n in factor_names}
    positive = {n: max(s, 0.0) for n, s in sharpes.items()}
    total = sum(positive.values())
    if total > 0:
        return {n: v / total for n, v in positive.items()}
    return {n: 1.0 / len(factor_names) for n in factor_names}


def _shrinkage_floor_weights(trailing: pd.DataFrame, factor_names: list,
                             prior_w: dict, shrink: float = 0.5, floor: float = 0.10) -> dict:
    """v2: チェイシング型の目標配分を、前回配分・等配分方向へシュリンクし、
    最低配分(floor)を強制することで極端な乗り換え・集中を抑える。
    """
    target = _sharpe_chasing_weights(trailing, factor_names)
    eq_w = 1.0 / len(factor_names)
    # 目標配分を「前回配分と等配分の平均」方向へシュリンク（急変を抑制）
    blended_prior = {n: 0.5 * prior_w[n] + 0.5 * eq_w for n in factor_names}
    w = {n: shrink * blended_prior[n] + (1 - shrink) * target[n] for n in factor_names}
    # 最低配分を強制し、残りを比例配分
    w = {n: max(v, floor) for n, v in w.items()}
    total = sum(w.values())
    return {n: v / total for n, v in w.items()}


def _risk_parity_weights(trailing: pd.DataFrame, factor_names: list) -> dict:
    """v3: リターンを追いかけず、各ファクターの直近ボラティリティの逆数で
    配分する（Dalio流リスクパリティを「銘柄間」でなく「ファクター間」に
    適用したもの）。良かった/悪かったを一切見ず、変動の大きさだけを見る。
    """
    inv_vol = {n: 1.0 / trailing[n].std() if trailing[n].std() else 0.0 for n in factor_names}
    total = sum(inv_vol.values())
    if total > 0:
        return {n: v / total for n, v in inv_vol.items()}
    return {n: 1.0 / len(factor_names) for n in factor_names}


def walk_forward_factor_rotation(close: pd.DataFrame, scores: dict,
                                 standalone_returns: pd.DataFrame,
                                 lookback: int = 504, method: str = "chasing") -> dict:
    """年次でファクター重みを更新するウォークフォワード。

    各評価日tでは standalone_returns.loc[:t] の末尾lookback日だけを使い、
    そこで決めた重みは**tより後、次の評価日まで**の期間に適用する
    （実装時、tまでのデータで決めた重みをtで終わる同じ期間に適用して
    しまう先読みバグがあり、その年自身のリターンが重み決定に混入して
    いた。評価日の翌日から次の評価日までへ適用するよう修正した）。

    method: "chasing"(v1・直近Sharpe比例)/"shrinkage"(v2・急変抑制+下限)/
           "risk_parity"(v3・ボラの逆数、リターンを追いかけない)。
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

    prior_w = {n: eq_w for n in factor_names}
    for i, t in enumerate(eval_dates):
        trailing = standalone_returns.loc[:t].iloc[-lookback:]
        if len(trailing) < lookback // 2:
            w = {n: eq_w for n in factor_names}  # データ不足期間は等配分
        elif method == "chasing":
            w = _sharpe_chasing_weights(trailing, factor_names)
        elif method == "shrinkage":
            w = _shrinkage_floor_weights(trailing, factor_names, prior_w)
        elif method == "risk_parity":
            w = _risk_parity_weights(trailing, factor_names)
        else:
            raise ValueError(f"unknown method: {method}")
        weight_history[t] = w
        prior_w = w

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

    ret_series = {}
    print("\n動的配分3手法の年次配分・成績:")
    for method, label in [("chasing", "v1チェイシング型"), ("shrinkage", "v2シュリンク+下限型"),
                          ("risk_parity", "v3リスクパリティ型")]:
        wf = walk_forward_factor_rotation(close, scores, standalone, lookback=504, method=method)
        res_wf = strategy.backtest(close, wf["blended_score"], top_q=0.2, rebalance="ME")
        m_wf = strategy.metrics(res_wf.returns, res_wf.equity)
        ret_series[method] = res_wf.returns
        print(f"\n--- {label} ---")
        for t, w in wf["weight_history"].items():
            w_str = "  ".join(f"{n}={v:.2f}" for n, v in w.items())
            print(f"  {t.date()}: {w_str}")
        print(f"  【{label}】 {strategy.format_metrics(m_wf)}")

    # 比較: 固定3ファクター・固定FXのみ
    fixed_3f = strategy.WEIGHTS["M"] * scores["Momentum"] + \
              strategy.WEIGHTS["sigma"] * (-scores["LowVol"]) + \
              strategy.WEIGHTS["L"] * scores["Liquidity"]
    res_3f = strategy.backtest(close, fixed_3f, top_q=0.2, rebalance="ME")
    m_3f = strategy.metrics(res_3f.returns, res_3f.equity)
    ret_series["fixed_3factor"] = res_3f.returns

    res_fx = strategy.backtest(close, scores["FX"], top_q=0.2, rebalance="ME")
    m_fx = strategy.metrics(res_fx.returns, res_fx.equity)
    ret_series["fixed_fx_only"] = res_fx.returns

    universe_eq = (close.mean(axis=1) / close.mean(axis=1).iloc[0])

    print("\n" + "=" * 78)
    print("全手法まとめ")
    print("=" * 78)
    for method, label in [("chasing", "v1チェイシング型　"), ("shrinkage", "v2シュリンク+下限型"),
                          ("risk_parity", "v3リスクパリティ型")]:
        m = strategy.metrics(ret_series[method], (1 + ret_series[method]).cumprod())
        print(f"  {label}: {strategy.format_metrics(m)}")
    print(f"  固定3ファクターのみ　: {strategy.format_metrics(m_3f)}")
    print(f"  固定FXのみ　　　　　: {strategy.format_metrics(m_fx)}")
    print(f"  （参考）ユニバース均等保有 最終={universe_eq.iloc[-1]:.2f}倍")

    # DSR/PBO: 3つの動的手法 + 固定3F + 固定FX の5通りを比較
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
    print(f"\nDSR/PBO比較（5通り: v1/v2/v3/固定3F/固定FX）:")
    print(f"  最良: {best_key}  DSR={dsr['dsr']:.3f}  PBO={pbo['pbo']:.3f}")


if __name__ == "__main__":
    main()
