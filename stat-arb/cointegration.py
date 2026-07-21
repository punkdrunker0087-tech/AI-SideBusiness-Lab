"""コインテグレーション ―― 「個々は非定常でも、ある組み合わせは定常か」を検定する。

- Engle-Granger法（二変量）: y = α + β・x + ε をOLS推定し、残差εにADF検定を
  かける。εが定常なら y と x はコインテグレーション関係にある（長期均衡）。
- Johansen法（多変量）: 3資産以上の組み合わせで同時に検定する（statsmodelsの
  VECM周りの実装を利用）。

参照:
  Engle, R. & Granger, C. (1987) "Co-integration and Error Correction"
  Johansen, S. (1991) "Estimation and Hypothesis Testing of Cointegration
  Vectors in Gaussian Vector Autoregressive Models"
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen


def engle_granger(y: pd.Series, x: pd.Series) -> dict:
    """二変量コインテグレーション検定（Engle-Granger）。

    statsmodels.coint はEngle-Granger法の標準実装（回帰→残差ADF検定を
    臨界値表つきで行う）。合わせて手動でのヘッジ比率も返す。
    """
    df = pd.concat([y, x], axis=1).dropna()
    if len(df) < 30:
        return {"p_value": np.nan, "hedge_ratio": np.nan, "n_obs": len(df)}

    t_stat, p_value, crit_values = coint(df.iloc[:, 0], df.iloc[:, 1])

    # ヘッジ比率（β）: y = α + β・x + ε のOLS推定
    X = np.column_stack([np.ones(len(df)), df.iloc[:, 1].values])
    beta, *_ = np.linalg.lstsq(X, df.iloc[:, 0].values, rcond=None)
    alpha, hedge_ratio = beta

    resid = df.iloc[:, 0].values - (alpha + hedge_ratio * df.iloc[:, 1].values)
    resid_adf_p = adfuller(resid, autolag="AIC")[1]

    return {
        "t_stat": float(t_stat), "p_value": float(p_value),
        "crit_1%": float(crit_values[0]), "crit_5%": float(crit_values[1]),
        "crit_10%": float(crit_values[2]),
        "hedge_ratio": float(hedge_ratio), "alpha": float(alpha),
        "resid_adf_p": float(resid_adf_p), "n_obs": len(df),
    }


def is_cointegrated(result: dict, alpha_level: float = 0.05) -> bool:
    return not np.isnan(result.get("p_value", np.nan)) and result["p_value"] < alpha_level


def johansen_test(prices: pd.DataFrame, det_order: int = 0, k_ar_diff: int = 1) -> dict:
    """多変量コインテグレーション検定（Johansen）。3資産以上向け。

    trace統計量が各階数(rank)の臨界値を上回るかで、コインテグレーション
    関係の本数（rank）を推定する。
    det_order: 0=定数項なしの決定的トレンド仮定（標準的な選択）
    """
    df = prices.dropna()
    if len(df) < 30 or df.shape[1] < 2:
        return {"rank": 0, "trace_stats": None}

    result = coint_johansen(df.values, det_order, k_ar_diff)
    trace_stats = result.lr1          # トレース統計量（各rank仮説）
    crit_95 = result.cvt[:, 1]        # 95%臨界値

    rank = 0
    for i in range(len(trace_stats)):
        if trace_stats[i] > crit_95[i]:
            rank = i + 1
        else:
            break

    return {
        "rank": rank,
        "trace_stats": trace_stats.tolist(),
        "crit_95": crit_95.tolist(),
        "eigenvectors": result.evec[:, 0].tolist() if rank > 0 else None,
        "n_obs": len(df),
    }
