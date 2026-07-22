"""Eugene Fama & Kenneth French の Factor Investing ―― "Common risk factors..." (1993)。

## ①原典 / ②要約
Fama & French (1993, *Journal of Financial Economics*) は、CAPMのβだけ
では株式リターンの断面を説明できないとし、3ファクターモデルを提示した:

  R_i − R_f = α + β(R_m − R_f) + s・SMB + h・HML + ε

  - **SMB**（Small Minus Big）: 小型株が大型株を上回る超過リターン
  - **HML**（High Minus Low）: 高PBR銘柄（バリュー株）が低PBR銘柄
    （グロース株）を上回る超過リターン

後にCarhart (1997) がMomentumを、Fama-French (2015) がProfitability・
Investmentを追加した5ファクターモデルへ拡張している。

## この戦略の位置づけ（差分のみ追加）
Size・Value・Quality・Momentum・LowVolの各ファクター構築ロジックは
既に`../multifactor-investing/factors.py`にある（本シリーズで重複
実装しない）。ここでは、そのモジュールをそのまま再利用し、**本シリーズの
10銘柄ユニバースでSMB(Size)・HML(Value)相当のファクターを構築した場合、
実際に断面リターンとどう関係するか**という差分だけを検証する。

⚠️ 重大な制約: Fama-Frenchの原典は数千銘柄の断面での統計的検定
（ファクターポートフォリオのt検定・R²）が前提。10銘柄では統計的な
有意性を云うことはそもそもできず、ここでの結果は「傾向の参考値」に
過ぎない。
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_MFI_PATH = str(Path(__file__).resolve().parent.parent / "multifactor-investing")
if _MFI_PATH not in sys.path:
    sys.path.append(_MFI_PATH)
import factors as mfi_factors  # noqa: E402


def build_size_value_score(fundamentals: pd.DataFrame) -> pd.DataFrame:
    """multifactor-investing.factors の Size・Value 定義をそのまま適用する。"""
    size = mfi_factors.size_snapshot(fundamentals)
    value_parts = mfi_factors.value_snapshot(fundamentals)
    value = value_parts.mean(axis=1)
    return pd.DataFrame({"size_score": size, "value_score": value})


def backtest_smb_hml_tilt(close: pd.DataFrame, scores: pd.DataFrame, top_n: int = 5) -> dict:
    """Sizeスコア上位(小型寄り)・Valueスコア上位(割安寄り)の各tiltを均等保有し、
    ユニバース平均・大型/グロース側と比較する。
    """
    small = scores["size_score"].sort_values(ascending=False).index[:top_n].tolist()
    big = scores["size_score"].sort_values(ascending=False).index[-top_n:].tolist()
    value = scores["value_score"].sort_values(ascending=False).index[:top_n].tolist()
    growth = scores["value_score"].sort_values(ascending=False).index[-top_n:].tolist()

    def eq(symbols):
        sub = close[symbols]
        return (sub.mean(axis=1) / sub.mean(axis=1).iloc[0])

    eq_small, eq_big = eq(small), eq(big)
    eq_value, eq_growth = eq(value), eq(growth)
    universe_eq = (close.mean(axis=1) / close.mean(axis=1).iloc[0])

    smb_series = eq_small - eq_big
    hml_series = eq_value - eq_growth

    return {
        "small": small, "big": big, "value": value, "growth": growth,
        "final_small": float(eq_small.iloc[-1]), "final_big": float(eq_big.iloc[-1]),
        "final_value": float(eq_value.iloc[-1]), "final_growth": float(eq_growth.iloc[-1]),
        "final_universe": float(universe_eq.iloc[-1]),
        "smb_final_spread": float(smb_series.iloc[-1]),
        "hml_final_spread": float(hml_series.iloc[-1]),
    }
