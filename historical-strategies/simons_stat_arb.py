"""Jim Simons / Renaissance Technologies の統計的裁定 ―― 学術的に検証可能な範囲。

## ①原典 / ②要約の限界
Renaissance TechnologiesのMedallion Fundの具体的シグナル・モデルは
一切公開されておらず（原典に相当する論文・書籍が存在しない）、公に
確認できるのは以下の性質だけ:

  - 短期の統計的パターン（価格の微小な非効率性）を大量のデータと
    機械学習・統計モデルで検出する
  - 個別の予測精度は低くても、大量の独立した小さなエッジを分散して
    積み上げることで安定した収益を狙う（"多数の弱いシグナルの集約"）
  - 数学者・統計学者中心のチームが、伝統的な財務分析ではなく統計的
    異常検知に徹する

これは「歴史上のある一つの手法」というより「統計的裁定という研究分野
そのもの」に近い。本シリーズでは、Simonsの哲学に最も近い**学術的に
再現可能な統計的裁定の一手法（コインテグレーションに基づくペア
トレーディング）**を、本シリーズのユニバースに適用する。

## この戦略の位置づけ（差分のみ追加）
コインテグレーション検定・ウォークフォワード平均回帰バックテストの
コア実装は既に`../stat-arb/`にある（`cointegration.py`・
`meanreversion.py`）。本シリーズで重複実装はせず、**本シリーズの
10銘柄ユニバースの中でコインテグレーション・ペアが見つかるか、
見つかった場合にウォークフォワードで機能するか**という差分だけを検証する。

⚠️ 重大な制約: 本ユニバースの10銘柄は業種・流動性を揃えた
ペア候補ではなく、Magic Formula等のための銘柄選定（時価総額上位・
多様な業種）である。Simons/統計的裁定が前提とする「大量の候補から
本当に安定した統計的関係を持つペアだけを厳選する」というプロセスの
入り口にすら立てていない可能性が高い。
"""
import itertools
import sys
from pathlib import Path

import pandas as pd

_SA_PATH = str(Path(__file__).resolve().parent.parent / "stat-arb")
if _SA_PATH not in sys.path:
    sys.path.append(_SA_PATH)
import cointegration as coint  # noqa: E402
import meanreversion as mr  # noqa: E402


def find_best_cointegrated_pair(close: pd.DataFrame, alpha_level: float = 0.05) -> dict:
    """ユニバース内の全ペアでEngle-Granger検定を行い、最もp値が小さいペアを返す。"""
    results = []
    for a, b in itertools.combinations(close.columns, 2):
        res = coint.engle_granger(close[a], close[b])
        res["pair"] = (a, b)
        results.append(res)
    results_df = pd.DataFrame(results).sort_values("p_value")
    n_cointegrated = int((results_df["p_value"] < alpha_level).sum())
    best = results_df.iloc[0].to_dict() if not results_df.empty else None
    return {"all_pairs": results_df, "n_pairs_tested": len(results_df),
           "n_cointegrated": n_cointegrated, "best_pair": best}


def backtest_best_pair(close: pd.DataFrame, best_pair_result: dict) -> dict:
    """最良ペアでウォークフォワード平均回帰バックテストを実行する。"""
    a, b = best_pair_result["pair"]
    bt = mr.backtest(close[a], close[b])
    bt["pair"] = (a, b)
    return bt
