"""共動性（市場との統合度）ファクター ―― 分散・共分散とは別角度の「相関」次元。

歪度と同じ動機: 「まだ試していない、既存2テーマと違う可能性が高い候補」
として、各銘柄がユニバース平均とどれだけ強く連動しているか
（平均相関＝市場への統合度）を横断比較する。

⚠️ 数学的には、これはベータ（FX/Rateベータと同じ「共分散/分散」の
仲間）に近い性質を持つため、既存のFX/Rateベータ・LowVol/IVOLとの
相関を①新規性ゲートで必ず確認する（歪度ほど独立性は高くない可能性
がある、という点を正直に明記する）。
"""
import numpy as np
import pandas as pd

import factors


def comovement_score(close: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """各銘柄・各日の、ユニバース平均リターンとのローリング相関を横断Zスコア化。

    高いスコア=ユニバース平均との相関が高い（市場に強く統合されている）銘柄。
    """
    ret = close.pct_change()
    universe_ret = ret.mean(axis=1)
    corr = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)
    for col in close.columns:
        corr[col] = ret[col].rolling(window).corr(universe_ret)
    return factors.zscore_cross(corr)
