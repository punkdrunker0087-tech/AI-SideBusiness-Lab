"""ポートフォリオの「エクスポージャー」―― 保有銘柄でなく、特性への偏りを見る。

バリュー・モメンタム・サイズへの偏りに加え、セクター・地域への偏りも
「どの特性にどれだけさらされているか」として同列に扱う。
"""
import numpy as np
import pandas as pd


def factor_exposure(weights: pd.Series, factor_z: pd.DataFrame) -> pd.Series:
    """各ファクターへの加重平均エクスポージャー（w・z）。"""
    w = weights.reindex(factor_z.index).fillna(0.0)
    return (factor_z.mul(w, axis=0)).sum()


def sector_exposure(weights: pd.Series, sectors: pd.Series) -> pd.Series:
    """セクター別の合計ウェイト（集中度の把握）。"""
    w = weights.reindex(sectors.index).fillna(0.0)
    return w.groupby(sectors).sum().sort_values(ascending=False)


def concentration_report(weights: pd.Series, factor_z: pd.DataFrame,
                         sectors: pd.Series, top_n: int = 3) -> str:
    """エクスポージャー・レポートを1枚の文字列で返す。"""
    fe = factor_exposure(weights, factor_z)
    se = sector_exposure(weights, sectors)
    top_names = weights.abs().sort_values(ascending=False).head(top_n)

    lines = ["=== ポートフォリオ・エクスポージャー ==="]
    lines.append("ファクター・エクスポージャー:")
    for name, val in fe.items():
        bar = "+" * int(abs(val) * 5) if val > 0 else "-" * int(abs(val) * 5)
        lines.append(f"  {name:10s} {val:+.2f}  {bar}")

    lines.append("\nセクター・エクスポージャー（上位）:")
    for name, val in se.head(5).items():
        lines.append(f"  {name:24s} {val*100:5.1f}%")

    lines.append(f"\n上位{top_n}銘柄の集中度: "
                 + ", ".join(f"{k} {v*100:.0f}%" for k, v in top_names.items()))
    return "\n".join(lines)
