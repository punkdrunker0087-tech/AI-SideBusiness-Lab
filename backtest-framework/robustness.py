"""Stage 5: ロバスト性評価 ―― モンテカルロ・ブートストラップ・感度分析。

「1本の綺麗なエクイティカーブ」は1つの実現値に過ぎない。同じ戦略でも
順序や標本が少し違えば結果は揺れる。その揺れの幅を測り、観測成績が
偶然の当たりでないかを見る。
"""
import numpy as np


def monte_carlo_shuffle(returns: np.ndarray, n_sims: int = 2000,
                        periods: int = 252, seed: int = 0) -> dict:
    """日次リターンの順序をシャッフルして、指標の分布を得る。

    シャッフルはリターンの順序依存（トレンド・連敗の塊）を壊すので、
    「並び順に依存する最大DD」等が実際どれだけ運に左右されるかを示す。
    返り値: 観測値と、シャッフル分布のパーセンタイル。
    """
    r = np.asarray(returns, float)
    r = r[~np.isnan(r)]
    rng = np.random.default_rng(seed)

    def _sharpe(x):
        return x.mean() / x.std(ddof=1) * np.sqrt(periods) if x.std(ddof=1) else np.nan

    def _maxdd(x):
        eq = np.cumprod(1 + x)
        return float((eq / np.maximum.accumulate(eq) - 1).min())

    obs_sharpe, obs_dd = _sharpe(r), _maxdd(r)
    sharpes, dds = np.empty(n_sims), np.empty(n_sims)
    for i in range(n_sims):
        p = rng.permutation(r)
        sharpes[i] = _sharpe(p)
        dds[i] = _maxdd(p)
    return {
        "observed_sharpe": float(obs_sharpe),
        "observed_max_dd": obs_dd,
        "maxdd_p05": float(np.percentile(dds, 5)),
        "maxdd_p50": float(np.percentile(dds, 50)),
        "maxdd_p95": float(np.percentile(dds, 95)),
        "maxdd_worst": float(dds.min()),
    }


def stationary_bootstrap(returns: np.ndarray, avg_block: float = 10.0,
                         n_boot: int = 2000, periods: int = 252,
                         seed: int = 0) -> dict:
    """定常ブートストラップでSharpeの信頼区間を得る。

    ブロック単位で再標本するので、リターンの自己相関を（近似的に）保つ。
    単純シャッフルより現実的な不確実性を反映する。
    """
    r = np.asarray(returns, float)
    r = r[~np.isnan(r)]
    T = len(r)
    rng = np.random.default_rng(seed)
    p = 1.0 / max(avg_block, 1.0)

    sharpes = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.empty(T, dtype=int)
        idx[0] = rng.integers(0, T)
        for t in range(1, T):
            idx[t] = rng.integers(0, T) if rng.random() < p else (idx[t - 1] + 1) % T
        x = r[idx]
        sharpes[b] = x.mean() / x.std(ddof=1) * np.sqrt(periods) if x.std(ddof=1) else np.nan

    sharpes = sharpes[~np.isnan(sharpes)]
    return {
        "sharpe_mean": float(sharpes.mean()),
        "sharpe_ci95_low": float(np.percentile(sharpes, 2.5)),
        "sharpe_ci95_high": float(np.percentile(sharpes, 97.5)),
        "prob_sharpe_positive": float((sharpes > 0).mean()),
    }


def parameter_sensitivity(metric_fn, grid: dict) -> dict:
    """パラメータ感度分析。

    metric_fn: パラメータ辞書 → 指標(float) を返す関数。
    grid: {パラメータ名: [候補,...]}。全組み合わせで metric_fn を評価。
    返り値: 各組み合わせの結果と、ロバスト性サマリ
      （良い成績が「点」でなく「面」で続いていれば頑健、孤立していれば過学習疑い）。
    """
    from itertools import product

    keys = list(grid)
    results = []
    for vals in product(*[grid[k] for k in keys]):
        params = dict(zip(keys, vals))
        try:
            m = metric_fn(params)
        except Exception:  # noqa: BLE001
            m = np.nan
        results.append({**params, "metric": m})

    metrics = np.array([r["metric"] for r in results], float)
    valid = metrics[~np.isnan(metrics)]
    return {
        "results": results,
        "n_combos": len(results),
        "frac_positive": float((valid > 0).mean()) if len(valid) else np.nan,
        "metric_mean": float(valid.mean()) if len(valid) else np.nan,
        "metric_std": float(valid.std()) if len(valid) else np.nan,
        "metric_best": float(valid.max()) if len(valid) else np.nan,
    }
