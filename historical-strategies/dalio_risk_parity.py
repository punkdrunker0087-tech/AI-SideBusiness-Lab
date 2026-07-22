"""Ray Dalio の All Weather / リスクパリティ ―― Bridgewater Associates。

## ①原典 / ②要約
Dalioの中心的主張は、伝統的な60/40ポートフォリオは「分散されているように
見えて実際は株式リスクに支配されている」（資本の60%が株式でも、
ボラティリティの約90%は株式由来）というもの。**ドル配分ではなく
リスク寄与を資産間で均等化する**リスクパリティにより、特定の経済局面
（成長・インフレの高低4象限）に依存しない「オールウェザー」な
ポートフォリオを目指す。Dalioはさらに、この機械的な配分を大きく崩さず
「10〜15の無相関なリターン源泉を持つこと」「未来は予測できないと
認めること」を原則としている。

## この戦略の位置づけ（差分のみ追加）
リスクパリティのコア実装（Equal Risk Contribution最適化）は既に
`../portfolio-optimization/risk_parity.py`にある。本シリーズで重複
実装はせず、**そのモジュールを本シリーズのユニバース（10銘柄・株式のみ）
に適用した場合の挙動**という差分だけを追加する。

⚠️ 重大な制約: Dalioの原典は株式・債券・コモディティ・金など
**複数の資産クラス**をまたいでリスクを均等化することが前提。本シリーズの
ユニバースは日本株10銘柄のみで、資産クラスの分散という原典の核心部分は
再現できていない。ここでの検証は「同一資産クラス内でのリスク均等化
だけでも効果があるか」という、より限定的な問いへの回答に過ぎない。
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_PO_PATH = str(Path(__file__).resolve().parent.parent / "portfolio-optimization")
if _PO_PATH not in sys.path:
    sys.path.append(_PO_PATH)
import risk_parity as rp  # noqa: E402


def backtest_risk_parity_vs_equal_weight(close: pd.DataFrame, cov_window: int = 252,
                                         rebalance_freq: str = "QE") -> dict:
    """`risk_parity.equal_risk_contribution`を四半期ごとに再計算し、等ウェイトと比較する。"""
    ret = close.pct_change()
    s = pd.Series(close.index, index=close.index)
    rebal_dates = s.resample(rebalance_freq).last().dropna().tolist()
    rebal_dates = [d for d in rebal_dates if d >= close.index[cov_window]]

    weights_over_time = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)
    risk_contrib_at_rebal = {}
    w_current = np.ones(len(close.columns)) / len(close.columns)
    for d in rebal_dates:
        window = ret.loc[:d].iloc[-cov_window:]
        cov = window.cov().values * 252
        w_current = rp.equal_risk_contribution(cov)
        risk_contrib_at_rebal[d] = rp.risk_contribution(w_current, cov)
        weights_over_time.loc[d] = w_current
    weights_over_time = weights_over_time.ffill().bfill()

    strat_ret = (weights_over_time.shift(1) * ret).sum(axis=1)
    equity_rp = (1 + strat_ret.fillna(0)).cumprod()
    equity_ew = (close.mean(axis=1) / close.mean(axis=1).iloc[0])

    dd_rp = (equity_rp / equity_rp.cummax() - 1).min()
    dd_ew = (equity_ew / equity_ew.cummax() - 1).min()
    vol_rp = strat_ret.std() * np.sqrt(252)
    vol_ew = equity_ew.pct_change().std() * np.sqrt(252)

    last_rc = list(risk_contrib_at_rebal.values())[-1] if risk_contrib_at_rebal else None
    return {
        "equity_risk_parity": equity_rp, "equity_equal_weight": equity_ew,
        "final_rp": float(equity_rp.iloc[-1]), "final_ew": float(equity_ew.iloc[-1]),
        "max_dd_rp": float(dd_rp), "max_dd_ew": float(dd_ew),
        "vol_rp": float(vol_rp), "vol_ew": float(vol_ew),
        "last_risk_contribution": pd.Series(last_rc, index=close.columns) if last_rc is not None else None,
        "weights_over_time": weights_over_time,
    }
