"""歪度（リターン分布の非対称性）ファクター ―― 数学的に真に独立な第3の情報軸候補。

## なぜこれを試すか
ユーザーからの再反論: 「試していないものがたくさんあるのに、価格データの
限界と結論してよいのか」。実際、直近に不合格となったReversal・IVOLは、
数学的に既存ファクターと近い性質を持っていた（Reversalは平均リターン
=1次モーメントの符号違い、IVOLは分散=2次モーメントの残差版で
LowVolと同系統）。真に異なる情報を試すなら、**1次・2次モーメントとは
数学的に独立な3次モーメント（歪度）**を試すべき、という指摘に応える。

## 原典
Bali, T., Cakici, N., & Whitelaw, R. (2011) "Maxing out: Stocks as
lotteries and the cross-section of expected returns", *Journal of
Financial Economics*。直近の最大日次リターン（MAX）が高い「宝くじ的」
銘柄は、投資家の宝くじ選好により割高になりやすく、将来リターンが
低いというアノマリー。歪度（正の歪度=上振れが大きい分布）も同種の
「宝くじ的」性質を捉える指標として使われる。

⚠️ Reversal・IVOLで学んだ教訓を活かし、符号は理論に基づいて事前に
決める（高歪度=割高で将来リターン低い、なので**低歪度を好む**方向を
主契約とする）。逆方向も参考として検証するが、両方を「試行」に
含めてDSRを計算すると符号フィッシングになる、という前回の反省を
踏まえ、主契約の符号だけで単独のグリッドサーチ・DSR/PBOを行う。
"""
import numpy as np
import pandas as pd

import factors


def skewness_score(close: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """日次リターンの歪度を横断Zスコア化する（符号は原典通り: 低歪度=高スコア）。

    高いスコア=歪度が低い（宝くじ的でない）銘柄。Bali et al.の知見に
    従えば、これらは将来相対的に高いリターンを持つと期待される。
    pandasの`rolling().skew()`（Fisher-Pearson標準化積率歪度、ベクトル化
    実装）を使う——scipy.stats.skewを`rolling().apply(raw=True)`で列ごと
    Python関数呼び出しすると225銘柄×15年で著しく遅いため。
    """
    logret = np.log(close / close.shift(1))
    skew = logret.rolling(window).skew()
    return factors.zscore_cross(-skew)
