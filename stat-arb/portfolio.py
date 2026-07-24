"""複数ペアの管理 ―― 特定業種への集中・共通リスク要因・流動性・相関を意識する。

個々のペアは市場中立でも、複数ペアが同じ業種・同じ共通リスク要因に
束ねられていれば、ポートフォリオ全体としては分散されていない。
"""
import numpy as np
import pandas as pd


def sector_concentration(pairs: list, sectors: pd.Series) -> pd.Series:
    """採用ペアの業種別本数（同一業種への集中を把握する）。

    pairs: [(銘柄A, 銘柄B), ...]
    """
    industries = []
    for a, b in pairs:
        industries.append(sectors.get(a, "不明"))
    return pd.Series(industries).value_counts()


def common_risk_exposure(pair_pnls: dict) -> pd.DataFrame:
    """各ペアの日次PnL変化間の相関（共通リスク要因への束ねられ方の代理指標）。

    pair_pnls: {"A-B": 累積PnL Series, ...}
    """
    changes = {name: pnl.diff() for name, pnl in pair_pnls.items()}
    df = pd.DataFrame(changes).dropna(how="all")
    return df.corr()


def portfolio_report(pairs: list, sectors: pd.Series, pair_pnls: dict,
                     liquidity: pd.Series = None) -> str:
    """複数ペア管理のサマリレポート。"""
    lines = ["=== 複数ペア管理レポート ==="]
    conc = sector_concentration(pairs, sectors)
    lines.append(f"採用ペア数: {len(pairs)}")
    lines.append("業種別の本数（集中度）:")
    for name, cnt in conc.items():
        flag = " ⚠️ 集中" if cnt >= len(pairs) * 0.5 and len(pairs) > 1 else ""
        lines.append(f"  {name:24s} {cnt}本{flag}")

    corr = common_risk_exposure(pair_pnls)
    if len(corr) > 1:
        iu = np.triu_indices_from(corr.values, k=1)
        avg_corr = np.nanmean(corr.values[iu])
        lines.append(f"\nペア間PnL相関の平均: {avg_corr:+.2f}"
                     + ("  ⚠️ 共通リスク要因への束ねられが強い" if avg_corr > 0.5 else ""))

    return "\n".join(lines)
