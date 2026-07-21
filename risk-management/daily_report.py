"""8. 毎朝確認する項目 ―― 全モジュールを束ねた運用前チェックリスト。

9節の思想（利益を伸ばすより、想定外損失を早く検知し、リスクを可視化し、
ルールを一貫適用する）を、毎朝1枚のレポートに落とす。
"""
import numpy as np
import pandas as pd

import drawdown
import limits as limits_mod
import liquidity as liq
import market_risk
import sizing


def morning_report(weights: pd.Series, close: pd.DataFrame, volume: pd.DataFrame,
                   equity: pd.Series, market_ret: pd.Series,
                   nav: float = 1e7,
                   risk_limits: limits_mod.RiskLimits = None,
                   dd_policy: drawdown.DrawdownPolicy = None) -> str:
    """運用開始前チェックリストを1枚の文字列で返す。"""
    risk_limits = risk_limits or limits_mod.RiskLimits()
    dd_policy = dd_policy or drawdown.DrawdownPolicy()
    returns = close.pct_change().dropna()
    lines = ["=" * 60, "毎朝のリスクチェックリスト", "=" * 60]

    # ① ポートフォリオ損益
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1
    lines.append(f"① 損益      : 累積 {total_ret*100:+.1f}%  "
                 f"前日 {equity.pct_change().iloc[-1]*100:+.2f}%")

    # ② エクスポージャー
    gross, net = weights.abs().sum(), weights.sum()
    top = weights.abs().sort_values(ascending=False).head(3)
    lines.append(f"② エクスポージャー: Gross {gross:.2f} / Net {net:+.2f}  "
                 f"上位偏り: {', '.join(f'{k} {v:.0%}' for k,v in top.items())}")

    # ③ ボラティリティ（前日比）
    cov = sizing.ann_cov(returns)
    pvol = sizing.portfolio_vol(weights, cov)
    cov_prev = sizing.ann_cov(returns.iloc[:-1])
    pvol_prev = sizing.portfolio_vol(weights, cov_prev)
    lines.append(f"③ 年率ボラ  : {pvol*100:.1f}%  (前日 {pvol_prev*100:.1f}%, "
                 f"{'↑' if pvol>pvol_prev else '↓'})")

    # ④ 相関（平常時 vs 直近）
    spike = market_risk.correlation_spike(returns)
    lines.append(f"④ 平均相関  : 直近 {spike['current']:.2f} / "
                 f"平常 {spike['baseline']:.2f}  上振れ {spike['spike']:+.2f}"
                 + ("  ⚠️分散が効きにくい" if spike['spike'] > 0.15 else ""))

    # ⑤ 流動性
    pos_value = weights * nav
    lrep = liq.liquidity_report(pos_value, close, volume)
    slow = lrep[lrep["流動性注意"]] if "流動性注意" in lrep else pd.DataFrame()
    lines.append(f"⑤ 流動性    : 想定売却日数>1日の銘柄 {len(slow)}件"
                 + (f"（{', '.join(slow['銘柄'])}）" if len(slow) else ""))

    # ⑥ VaR / ストレス
    var99 = limits_mod.parametric_var(returns, weights)
    hvar = limits_mod.historical_var(returns @ weights.reindex(returns.columns).fillna(0))
    stress = market_risk.stress_test(weights, returns)
    worst = stress.loc[stress["損益(対NAV)"].idxmin()]
    lines.append(f"⑥ VaR/ストレス: 日次99%VaR {var99*100:.1f}%(パラメトリック)/"
                 f"{hvar*100:.1f}%(ヒストリカル)  "
                 f"最悪シナリオ {worst['シナリオ']} {worst['損益(対NAV)']*100:+.1f}%")

    # ⑦ ドローダウン対応
    dd = drawdown.current_state(equity, dd_policy)
    lines.append(f"⑦ DD対応    : 現在DD {dd['drawdown']*100:.1f}% → {dd['action']}")

    # ⑧ 制約違反
    breaches = limits_mod.check(weights, returns, risk_limits, dd["drawdown"])
    violated = breaches[breaches["違反"]]
    if len(violated):
        lines.append("⑧ 制約違反  : ⚠️ " + "  ".join(
            f"{r['項目']}({r['現状']:.2f}>{r['上限']:.2f})" for _, r in violated.iterrows()))
    else:
        lines.append("⑧ 制約違反  : ○ なし（全制約内）")

    return "\n".join(lines)
