"""パフォーマンス分析 ―― リターンを市場・ファクター寄与・銘柄固有・コストに分解する。

portfolio_return[t] = α + β_mkt・market_ret[t] + Σ_f β_f・factor_ret_f[t] + ε[t]

各ファクターリターン系列（`correlation.factor_return_series`の出力）に対する
時系列回帰（OLS）で β を推定し、寄与 = β_f × ファクターリターンの期間合計を
「どこから成果が生まれたか」として提示する。ε（残差）が銘柄固有要因。
"""
import numpy as np
import pandas as pd


def factor_regression(port_ret: pd.Series, market_ret: pd.Series,
                      factor_returns: dict) -> dict:
    """時系列OLSでβを推定する。返り値: {"beta": Series, "alpha": float, "r2": float,
    "residual": Series}。
    """
    names = list(factor_returns)
    X = pd.DataFrame({"market": market_ret, **factor_returns})
    df = pd.concat([port_ret.rename("port"), X], axis=1).dropna()
    y = df["port"].values
    X_mat = np.column_stack([np.ones(len(df)), df["market"].values,
                             *[df[n].values for n in names]])
    beta, *_ = np.linalg.lstsq(X_mat, y, rcond=None)
    alpha = beta[0]
    betas = pd.Series(beta[1:], index=["market"] + names)

    fitted = X_mat @ beta
    resid = y - fitted
    ss_res, ss_tot = np.sum(resid ** 2), np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else np.nan

    return {
        "alpha_daily": float(alpha),
        "beta": betas,
        "r2": float(r2),
        "residual": pd.Series(resid, index=df.index),
        "n_obs": len(df),
    }


def contribution_report(port_ret: pd.Series, market_ret: pd.Series,
                        factor_returns: dict, cost_drag: float = 0.0) -> pd.DataFrame:
    """期間トータルのリターンを「市場・各ファクター・αと残差・コスト」に分解する。

    寄与 = β_f × Σ(factor_ret_f)（線形近似。厳密な複利分解ではない簡易版）。
    """
    reg = factor_regression(port_ret, market_ret, factor_returns)
    names = list(factor_returns)
    all_series = {"market": market_ret, **factor_returns}

    rows = []
    for name in ["market"] + names:
        beta = reg["beta"][name]
        total_factor_ret = all_series[name].reindex(reg["residual"].index).sum()
        rows.append({"要因": name, "β": beta, "寄与(概算)": beta * total_factor_ret})

    alpha_total = reg["alpha_daily"] * reg["n_obs"]
    residual_total = reg["residual"].sum()
    rows.append({"要因": "α(切片)", "β": np.nan, "寄与(概算)": alpha_total})
    rows.append({"要因": "残差(銘柄固有)", "β": np.nan, "寄与(概算)": residual_total})
    rows.append({"要因": "取引コスト", "β": np.nan, "寄与(概算)": -abs(cost_drag)})

    df = pd.DataFrame(rows)
    df["R2"] = reg["r2"]
    return df
