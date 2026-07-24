"""ロバスト性 ―― 推定誤差・相関変化・ボラティリティ変化に結果が過度に振れないか。"""
import numpy as np
import pandas as pd


def shift_correlation(cov: np.ndarray, shock: float) -> np.ndarray:
    """相関がshock分だけ1へ収束するストレスを与える（危機時の相関上昇を模す）。

    分散（対角成分）は変えず、相関構造だけをシフトする。
    """
    std = np.sqrt(np.diag(cov))
    corr = cov / np.outer(std, std)
    stressed_corr = corr * (1 - shock) + shock * np.ones_like(corr)
    np.fill_diagonal(stressed_corr, 1.0)
    return stressed_corr * np.outer(std, std)


def vol_shock(cov: np.ndarray, mult: float) -> np.ndarray:
    """全資産のボラティリティをmult倍にするショック（分散はmult^2倍）。"""
    return cov * (mult ** 2)


def portfolio_vol(weights: np.ndarray, cov: np.ndarray) -> float:
    return float(np.sqrt(weights @ cov @ weights))


def scenario_report(weights_by_method: dict, cov_base: np.ndarray) -> pd.DataFrame:
    """各手法の重みについて、平常時・相関ストレス・ボラ急騰時のリスクを比較する。"""
    scenarios = {
        "平常時": cov_base,
        "相関収束(+0.3)": shift_correlation(cov_base, 0.3),
        "相関収束(危機・+0.6)": shift_correlation(cov_base, 0.6),
        "ボラ急騰(×2)": vol_shock(cov_base, 2.0),
    }
    rows = []
    for method, w in weights_by_method.items():
        row = {"手法": method}
        for name, cov in scenarios.items():
            row[name] = portfolio_vol(w, cov)
        rows.append(row)
    return pd.DataFrame(rows).set_index("手法")


def weight_stability_report(stability: dict, asset_names: list) -> pd.DataFrame:
    """推定誤差ブートストラップの結果を読みやすい表にする。"""
    return pd.DataFrame({
        "平均配分": stability["mean_weights"],
        "標準偏差": stability["std_weights"],
        "最小": stability["min_weights"],
        "最大": stability["max_weights"],
    }, index=asset_names).round(4)
