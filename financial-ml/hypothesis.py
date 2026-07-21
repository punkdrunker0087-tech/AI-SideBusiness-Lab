"""1. 研究仮説 ―― どのような市場現象をモデル化したいかを定義する。

「精度の高いモデル」でなく「将来データでも再現するモデル」を目指すため、
何を・なぜモデル化するのかを先に言語化する。
"""
from dataclasses import dataclass


@dataclass
class ResearchHypothesis:
    question: str            # モデル化したい市場現象
    rationale: str            # 経済的・行動的根拠
    target: str                # 予測対象（ラベル）
    horizon_days: int          # 予測ホライズン


HYPOTHESIS = ResearchHypothesis(
    question="モメンタム・ボラティリティ・出来高等の特徴量から、"
            "20日先の相対リターン（銘柄横断の順位）を予測できるか",
    rationale="投資家の情報反映の遅れ・リスク回避行動・流動性プレミアムが"
             "複合的に将来リターンに影響するという仮説（複数の学術的アノマリー"
             "の組み合わせ）。単一特徴量でなく複数モデルで非線形な相互作用を"
             "捉えられるかも検証する",
    target="forward_return_20d_rank",
    horizon_days=20,
)
