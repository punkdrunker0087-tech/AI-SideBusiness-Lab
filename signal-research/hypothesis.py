"""1. 仮説立案 ―― 「何でも試す」前に、なぜ効くはずかを言語化する。

シグナル探索は仮説から始める。仮説を先に固定することで、後の検証結果を
「なぜ効いた/効かなかったか」で解釈でき、データスヌーピング（下手な鉄砲）を防ぐ。
"""
from dataclasses import dataclass, field


@dataclass
class Hypothesis:
    name: str
    rationale: str                 # なぜ効くはずか（市場・投資家行動の仮説）
    feature: str                   # 検証する特徴量
    expected_sign: int             # +1: 高いほど将来リターン高い / -1: 逆
    horizon_days: int = 20         # 想定する効果の時間軸
    notes: str = ""

    def verdict(self, observed_ic: float) -> str:
        """観測ICが仮説の符号と整合するかを返す。"""
        if observed_ic * self.expected_sign > 0.02:
            return "○ 仮説の方向で予測力あり"
        if observed_ic * self.expected_sign < -0.02:
            return "× 仮説と逆方向（要再解釈）"
        return "△ 予測力ほぼなし"


# 本フレームワークで検証する仮説群（AQMの4ファクターに対応）
REGISTRY = [
    Hypothesis(
        name="中期モメンタム",
        rationale="投資家の反応は遅れる。上昇トレンドはしばらく継続する（過小反応）",
        feature="momentum_120", expected_sign=+1, horizon_days=20,
    ),
    Hypothesis(
        name="低ボラティリティ",
        rationale="高ボラ銘柄は宝くじ選好で買われ過ぎ、リスク調整後リターンは低い",
        feature="volatility_20", expected_sign=-1, horizon_days=20,
    ),
    Hypothesis(
        name="流動性",
        rationale="流動性の高い銘柄はスプレッドが狭く、需給ショックを受けにくい",
        feature="liquidity_log", expected_sign=+1, horizon_days=20,
    ),
    Hypothesis(
        name="短期リバーサル",
        rationale="直近の急騰急落は過剰反応で、短期では反転しやすい",
        feature="reversal_5", expected_sign=-1, horizon_days=5,
    ),
]
