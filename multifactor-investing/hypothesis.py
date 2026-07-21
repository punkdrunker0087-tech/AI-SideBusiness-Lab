"""1. 仮説設定 ―― なぜそのファクターが機能すると考えられるか。

5大ファクターそれぞれの経済的根拠を先に言語化する。検証（IC評価）の前に
仮説を固定することで、結果を「なぜ効いた/効かなかったか」で解釈できる。
"""
from dataclasses import dataclass


@dataclass
class FactorHypothesis:
    name: str
    rationale: str          # 経済的根拠
    expected_sign: int      # +1: スコアが高いほど将来リターンが高い
    data_type: str          # "price"(全期間先読みなし) / "snapshot"(現在値のみ)


REGISTRY = [
    FactorHypothesis(
        name="Value",
        rationale="割安な資産は市場の悲観・見落としを反映しており、"
                  "ファンダメンタルズへの回帰で長期的に報われる",
        expected_sign=+1, data_type="snapshot",
    ),
    FactorHypothesis(
        name="Momentum",
        rationale="投資家の情報反映は遅れる（過小反応）ため、"
                  "既存トレンドはしばらく継続する",
        expected_sign=+1, data_type="price",
    ),
    FactorHypothesis(
        name="Quality",
        rationale="収益性・財務健全性の高い企業はリスクが低く、"
                  "市場はこれを過小評価しがち",
        expected_sign=+1, data_type="snapshot",
    ),
    FactorHypothesis(
        name="Size",
        rationale="小型株は流動性・情報リスクのプレミアムを持ち、"
                  "大型株よりリスク調整後リターンが高い可能性がある",
        expected_sign=+1, data_type="snapshot",
    ),
    FactorHypothesis(
        name="LowVol",
        rationale="高ボラ資産は宝くじ選好・レバレッジ制約で買われ過ぎ、"
                  "低ボラ資産の方がリスク調整後で優れる（低ボラ・アノマリー）",
        expected_sign=+1, data_type="price",
    ),
]
