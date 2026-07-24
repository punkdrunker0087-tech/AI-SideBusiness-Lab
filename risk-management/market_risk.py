"""5. 相関監視 & 6. ストレステスト。

相関: 平常時は分散されていても、ストレス時に相関が跳ね上がる（分散が効かなくなる）。
      ローリング相関の平均を追い、急上昇を検知する。
ストレス: 過去の急変（暴落・ボラ急騰）を模したショックをポートに当て、耐性を見る。
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


# --- 5. 相関監視 ---
def avg_pairwise_correlation(returns: pd.DataFrame, window: int = 60) -> pd.Series:
    """ローリング平均ペア相関の時系列（分散の効き具合の代理指標）。"""
    out = {}
    cols = returns.columns
    for end in range(window, len(returns) + 1):
        sub = returns.iloc[end - window:end]
        corr = sub.corr().values
        iu = np.triu_indices_from(corr, k=1)
        out[returns.index[end - 1]] = np.nanmean(corr[iu])
    return pd.Series(out, name="avg_corr")


def correlation_spike(returns: pd.DataFrame, window: int = 60,
                      calm_window: int = 250) -> dict:
    """直近の平均相関が、平常時よりどれだけ上振れしているか。"""
    ac = avg_pairwise_correlation(returns, window)
    if len(ac) < 2:
        return {"current": np.nan, "baseline": np.nan, "spike": np.nan}
    current = float(ac.iloc[-1])
    baseline = float(ac.iloc[-min(calm_window, len(ac)):].median())
    return {"current": current, "baseline": baseline, "spike": current - baseline}


def stress_correlation(returns: pd.DataFrame, market: pd.Series,
                       stress_quantile: float = 0.05) -> pd.DataFrame:
    """市場が大きく下げた日（下位quantile）だけの相関 vs 平常時の相関。"""
    aligned = returns.join(market.rename("_mkt"), how="inner")
    thr = aligned["_mkt"].quantile(stress_quantile)
    stress = aligned[aligned["_mkt"] <= thr][returns.columns]
    calm = aligned[aligned["_mkt"] > thr][returns.columns]

    def _avg(df):
        c = df.corr().values
        iu = np.triu_indices_from(c, k=1)
        return np.nanmean(c[iu])

    return pd.DataFrame({
        "平常時 平均相関": [_avg(calm)],
        "ストレス時 平均相関": [_avg(stress)],
        "上昇幅": [_avg(stress) - _avg(calm)],
    })


# --- 6. ストレステスト ---
DEFAULT_SCENARIOS = {
    "一律ショック -10%": {"shock": -0.10},
    "一律ショック -20%": {"shock": -0.20},
    "ボラ急騰(2σの1日下落)": {"sigma_mult": -2.0},
    "ボラ急騰(3σの1日下落)": {"sigma_mult": -3.0},
}


def stress_test(weights: pd.Series, returns: pd.DataFrame,
                scenarios: dict = None) -> pd.DataFrame:
    """各シナリオでのポートフォリオ損益（対NAV）を返す。"""
    scenarios = scenarios or DEFAULT_SCENARIOS
    w = weights.reindex(returns.columns).fillna(0.0)
    daily_sigma = returns.std()
    rows = []
    for name, sc in scenarios.items():
        if "shock" in sc:
            pnl = float((w * sc["shock"]).sum())         # 全銘柄一律%下落
        elif "sigma_mult" in sc:
            shock = daily_sigma * sc["sigma_mult"]        # 各銘柄をσ倍動かす
            pnl = float((w * shock).sum())
        else:
            pnl = np.nan
        rows.append({"シナリオ": name, "損益(対NAV)": pnl})
    return pd.DataFrame(rows)
