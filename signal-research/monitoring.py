"""8. 運用後の監視 ―― 研究で有効でも、実運用で性能は変化する。

シグナル分布のドリフト、入力の変化、データ品質を継続監視する。
中心は PSI (Population Stability Index): 分布が学習時からどれだけズレたか。
"""
import numpy as np
import pandas as pd


def population_stability_index(expected: np.ndarray, actual: np.ndarray,
                               bins: int = 10) -> float:
    """PSI: 期待分布(学習時) と 実分布(運用時) のズレ。

    目安: <0.1 安定 / 0.1〜0.25 要注意 / >0.25 大きく変化（モデル見直し）。
    """
    expected = np.asarray(expected, float)
    expected = expected[~np.isnan(expected)]
    actual = np.asarray(actual, float)
    actual = actual[~np.isnan(actual)]
    if len(expected) < bins or len(actual) < bins:
        return np.nan
    # 期待分布の分位でビン境界を作る
    edges = np.percentile(expected, np.linspace(0, 100, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    e_pct = np.histogram(expected, edges)[0] / len(expected)
    a_pct = np.histogram(actual, edges)[0] / len(actual)
    e_pct = np.clip(e_pct, 1e-6, None)
    a_pct = np.clip(a_pct, 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def psi_verdict(psi: float) -> str:
    if np.isnan(psi):
        return "判定不能（データ不足）"
    if psi < 0.1:
        return "○ 安定"
    if psi < 0.25:
        return "△ 要注意（分布がずれ始めている）"
    return "⚠️ 大きく変化（モデル・特徴量の見直し）"


def rolling_signal_stats(feature: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """シグナルの横断平均・分散・欠損率の推移（入力ドリフト・品質の監視）。"""
    daily_mean = feature.mean(axis=1)
    daily_std = feature.std(axis=1)
    missing = feature.isna().mean(axis=1)
    return pd.DataFrame({
        "signal_mean": daily_mean.rolling(window).mean(),
        "signal_std": daily_std.rolling(window).mean(),
        "missing_rate": missing.rolling(window).mean(),
    })


def drift_report(feature: pd.DataFrame, split: float = 0.5) -> dict:
    """特徴量の前半(学習相当)と後半(運用相当)でPSIを計算し、ドリフトを見る。"""
    vals = feature.values.flatten()
    vals = vals[~np.isnan(vals)]
    cut = int(len(vals) * split)
    psi = population_stability_index(vals[:cut], vals[cut:])
    return {"psi": psi, "verdict": psi_verdict(psi)}
