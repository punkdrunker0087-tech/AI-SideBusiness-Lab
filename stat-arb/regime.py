"""レジーム変化 ―― 統計的な関係は永続しない。構造変化・相関構造の変化を監視する。

- ローリング・コインテグレーション: 過去の関係が「今も」定常かを、窓をずらして
  ADF検定のp値を追跡する。p値が悪化トレンドなら関係の崩壊を疑う。
- ローリング相関・ボラティリティ: 関係の強さと市場環境の変化を並べて見る。
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller


def rolling_coint_pvalue(spread: pd.Series, window: int = 120, step: int = 5) -> pd.Series:
    """窓をずらしながら、その窓内でスプレッドが定常かのADF p値を計算する。

    p値が時間とともに上昇（有意でなくなる）していれば、コインテグレーション
    関係が崩れつつある兆候。
    """
    s = spread.dropna()
    out = {}
    for end in range(window, len(s) + 1, step):
        w = s.iloc[end - window:end]
        try:
            p = adfuller(w, autolag="AIC")[1]
        except Exception:  # noqa: BLE001
            p = np.nan
        out[s.index[end - 1]] = p
    return pd.Series(out, name="coint_pvalue")


def rolling_correlation(y: pd.Series, x: pd.Series, window: int = 60) -> pd.Series:
    df = pd.concat([y, x], axis=1).dropna()
    return df.iloc[:, 0].rolling(window).corr(df.iloc[:, 1])


def structural_break_report(spread: pd.Series, window: int = 120,
                            alpha: float = 0.05) -> dict:
    """直近窓と、それ以前の窓でp値・スプレッド分散を比較し、崩壊の兆候を要約する。"""
    roll_p = rolling_coint_pvalue(spread, window)
    if len(roll_p) < 2:
        return {"verdict": "判定不能（データ不足）"}

    recent_p = roll_p.iloc[-1]
    earlier_p = roll_p.iloc[:-1].median()
    s = spread.dropna()
    recent_std = s.iloc[-window:].std()
    earlier_std = s.iloc[:-window].std() if len(s) > window * 2 else recent_std

    breaking = recent_p > alpha and earlier_p <= alpha
    verdict = (
        "⚠️ 直近で関係が崩れた可能性（以前は定常、直近は非定常）" if breaking
        else "○ 関係は概ね維持" if recent_p <= alpha
        else "△ 直近も以前も非定常（そもそも弱い関係）"
    )
    return {
        "recent_pvalue": float(recent_p), "earlier_median_pvalue": float(earlier_p),
        "recent_std": float(recent_std), "earlier_std": float(earlier_std),
        "vol_ratio": float(recent_std / earlier_std) if earlier_std else np.nan,
        "verdict": verdict,
    }
