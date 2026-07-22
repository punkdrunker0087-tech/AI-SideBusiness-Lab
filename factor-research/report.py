"""9. レポーティング ―― リターン推移・リスク指標・ドローダウン・ファクター別寄与・
市場環境ごとの比較を1つの研究レポートにまとめ、解釈と再現性を高める。
"""
import datetime

import pandas as pd


def build_report(universe_log: str, factor_results: dict, regime_results: dict,
                 capacity_results: dict, portfolio_results: dict) -> str:
    """全セクションを1つのMarkdown文字列にまとめる。"""
    lines = [
        "# 学術的ファクター研究レポート",
        f"生成日時: {datetime.datetime.now().isoformat()}",
        "",
        "## 1. 研究目的",
        "経済的な説明があるか・異なる市場/期間で再現するか・コストや制約を",
        "考慮しても特徴が維持されるか、を過去リターンの高さより重視する。",
        "",
        "## 2. 投資ユニバース",
        "```", universe_log, "```",
        "",
        "## 3-5. ファクター別リターン・リスク評価",
    ]

    rows = []
    for name, r in factor_results.items():
        rows.append({
            "ファクター": name, "年率リターン": r["ann_return"],
            "ボラ": r["risk"]["volatility"], "Sharpe": r["risk"]["sharpe"],
            "Sortino": r["risk"]["sortino"], "Calmar": r["risk"]["calmar"],
            "最大DD": r["risk"]["max_drawdown"], "VaR95": r["risk"]["var_95"],
        })
    lines.append(pd.DataFrame(rows).round(4).to_markdown(index=False))

    lines += ["", "## 6. 市場環境ごとの分析（強気/弱気レジーム別Sharpe）"]
    for name, reg_df in regime_results.items():
        if reg_df.empty:
            continue
        lines.append(f"\n### {name}")
        lines.append(reg_df[["sharpe", "max_drawdown", "n_days"]].round(3).to_markdown())

    lines += ["", "## 7. 実装可能性（キャパシティ分析）"]
    for name, cap in capacity_results.items():
        parts = []
        for k, v in cap.items():
            pct = k.split("_")[1]
            parts.append(f"エッジの{pct}が消えるAUM ≈ {v:.0f}億円" if v
                        else f"エッジの{pct}: 検証範囲内で到達せず")
        lines.append(f"- **{name}**: " + ", ".join(parts))

    lines += ["", "## 8. ポートフォリオ評価（複数ファクター合成）"]
    lines.append(f"分散化比率: {portfolio_results['diversification_ratio']:.2f}")
    lines.append("\nファクター間相関:")
    lines.append(portfolio_results["correlation"].round(2).to_markdown())
    lines.append("\n年率回転率:")
    lines.append(portfolio_results["turnover"].round(2).to_markdown(index=False))

    lines += [
        "", "## 研究で重視される原則（チェックリスト）",
        "- [x] 仮説を先に定義する（各ファクターの経済的根拠）",
        "- [x] 将来情報を排除する（モメンタムは価格ベースで先読みなし。"
        "Value/Quality/Sizeはライブ断面専用と明示）",
        "- [x] 複数の期間・市場環境で検証する（レジーム別分析）",
        "- [x] 取引コスト・流動性を考慮する（キャパシティ分析）",
        "- [ ] 統計的有意性の厳密な検定（`../backtest-framework/`のDSR/PBOを別途適用推奨）",
    ]

    return "\n".join(lines)
