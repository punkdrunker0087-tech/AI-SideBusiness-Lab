"""統計評価 ―― Sharpe比だけに頼らない、過学習に強い有意性評価。

実装する指標:
  - sharpe / sortino / information_ratio : 基本のリスク調整リターン
  - probabilistic_sharpe_ratio (PSR)      : Sharpeが基準を上回る確率
  - deflated_sharpe_ratio (DSR)           : 多重検定・非正規性を補正したSharpe有意性
  - pbo_cscv                              : Probability of Backtest Overfitting
  - whites_reality_check                  : データスヌーピングを補正した優位性検定

参照:
  Bailey & López de Prado (2014) "The Deflated Sharpe Ratio"
  Bailey, Borwein, López de Prado, Zhu (2015) "The Probability of Backtest Overfitting"
  White (2000) "A Reality Check for Data Snooping"
"""
import numpy as np
from scipy import stats

TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# 基本指標
# ---------------------------------------------------------------------------
def sharpe(returns: np.ndarray, periods: int = TRADING_DAYS) -> float:
    r = np.asarray(returns, float)
    r = r[~np.isnan(r)]
    if r.std(ddof=1) == 0 or len(r) < 2:
        return np.nan
    return r.mean() / r.std(ddof=1) * np.sqrt(periods)


def sortino(returns: np.ndarray, periods: int = TRADING_DAYS) -> float:
    r = np.asarray(returns, float)
    r = r[~np.isnan(r)]
    downside = r[r < 0].std(ddof=1)
    if downside == 0 or np.isnan(downside):
        return np.nan
    return r.mean() / downside * np.sqrt(periods)


def information_ratio(returns: np.ndarray, benchmark: np.ndarray,
                      periods: int = TRADING_DAYS) -> float:
    active = np.asarray(returns, float) - np.asarray(benchmark, float)
    active = active[~np.isnan(active)]
    if active.std(ddof=1) == 0:
        return np.nan
    return active.mean() / active.std(ddof=1) * np.sqrt(periods)


# ---------------------------------------------------------------------------
# Probabilistic / Deflated Sharpe Ratio
# ---------------------------------------------------------------------------
def probabilistic_sharpe_ratio(returns: np.ndarray, sr_benchmark: float = 0.0) -> float:
    """PSR: 観測Sharpeが基準Sharpeを真に上回る確率（歪度・尖度で補正）。

    返り値は確率(0〜1)。すべて *1観測あたり* のSharpeで計算（年率化しない）。
    """
    r = np.asarray(returns, float)
    r = r[~np.isnan(r)]
    n = len(r)
    if n < 3 or r.std(ddof=1) == 0:
        return np.nan
    sr = r.mean() / r.std(ddof=1)                  # per-period Sharpe
    skew = stats.skew(r)
    kurt = stats.kurtosis(r, fisher=False)          # 非過剰尖度（正規=3）
    denom = np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    if denom == 0:
        return np.nan
    z = (sr - sr_benchmark) * np.sqrt(n - 1) / denom
    return float(stats.norm.cdf(z))


def expected_max_sharpe(sr_variance: float, n_trials: int) -> float:
    """N回試行したとき、無効な戦略群でも偶然得られる期待最大Sharpe（1観測あたり）。

    López de Prado の近似式。多重検定の"下駄"の大きさ。
    """
    if n_trials < 2 or sr_variance <= 0:
        return 0.0
    gamma = 0.5772156649015329  # オイラー・マスケローニ定数
    e = np.e
    z1 = stats.norm.ppf(1 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1 - 1.0 / (n_trials * e))
    return np.sqrt(sr_variance) * ((1 - gamma) * z1 + gamma * z2)


def deflated_sharpe_ratio(returns: np.ndarray, sr_trials: np.ndarray) -> dict:
    """DSR: 多重検定・非正規性を補正したSharpeの有意性。

    sr_trials: 試したすべての戦略の（同一頻度・1観測あたりの）Sharpe配列。
      これが「何回試したか」の情報を担う。多いほど基準が上がる。
    返り値: {"dsr": 確率, "sr_observed": ..., "sr_expected_max": ..., "n_trials": ...}
    """
    sr_trials = np.asarray(sr_trials, float)
    sr_trials = sr_trials[~np.isnan(sr_trials)]
    k = len(sr_trials)
    sr0 = expected_max_sharpe(sr_trials.var(ddof=1) if k > 1 else 0.0, k)
    dsr = probabilistic_sharpe_ratio(returns, sr_benchmark=sr0)
    r = np.asarray(returns, float)
    r = r[~np.isnan(r)]
    sr_obs = r.mean() / r.std(ddof=1) if r.std(ddof=1) else np.nan
    return {
        "dsr": dsr,
        "sr_observed_per_period": float(sr_obs),
        "sr_expected_max_per_period": float(sr0),
        "n_trials": k,
    }


# ---------------------------------------------------------------------------
# Probability of Backtest Overfitting (CSCV法)
# ---------------------------------------------------------------------------
def pbo_cscv(returns_matrix: np.ndarray, n_splits: int = 10) -> dict:
    """PBO: 「イン最良の戦略が、アウトで中央値以下に落ちる確率」。

    returns_matrix: shape (T, N)。T=時点, N=戦略数。各列が1戦略の時系列リターン。
    n_splits(S): 時間をS個の等分ブロックに割る（偶数）。S/2をIS・残りをOOSにする
                 全組み合わせ C(S, S/2) を評価する（CSCV）。
    返り値: {"pbo": 過学習確率, "n_combinations": ...}
    """
    from itertools import combinations

    R = np.asarray(returns_matrix, float)
    T, N = R.shape
    if N < 2:
        return {"pbo": np.nan, "n_combinations": 0}
    if n_splits % 2 == 1:
        n_splits += 1
    # T をS個のブロックに分割
    idx = np.array_split(np.arange(T), n_splits)
    blocks = list(range(n_splits))

    logits = []
    for is_blocks in combinations(blocks, n_splits // 2):
        os_blocks = [b for b in blocks if b not in is_blocks]
        is_rows = np.concatenate([idx[b] for b in is_blocks])
        os_rows = np.concatenate([idx[b] for b in os_blocks])
        # IS/OOS の各戦略Sharpe（1観測あたりで十分・順位のみ使う）
        def _sr(rows):
            sub = R[rows]
            mu = sub.mean(axis=0)
            sd = sub.std(axis=0, ddof=1)
            sd[sd == 0] = np.nan
            return mu / sd
        sr_is = _sr(is_rows)
        sr_os = _sr(os_rows)
        best = np.nanargmax(sr_is)              # IS最良の戦略
        # その戦略のOOS順位（相対順位ω）
        order = stats.rankdata(sr_os)           # 1..N（大きいほど良い）
        omega = order[best] / (N + 1)
        omega = min(max(omega, 1e-6), 1 - 1e-6)
        logits.append(np.log(omega / (1 - omega)))

    logits = np.array(logits)
    pbo = float((logits <= 0).mean())           # λ≤0 = OOSで中央値以下
    return {"pbo": pbo, "n_combinations": len(logits)}


# ---------------------------------------------------------------------------
# White's Reality Check（定常ブートストラップ）
# ---------------------------------------------------------------------------
def _stationary_bootstrap_indices(T: int, avg_block: float, rng) -> np.ndarray:
    """Politis-Romano 定常ブートストラップのインデックス列を生成。"""
    p = 1.0 / max(avg_block, 1.0)
    idx = np.empty(T, dtype=int)
    idx[0] = rng.integers(0, T)
    for t in range(1, T):
        if rng.random() < p:
            idx[t] = rng.integers(0, T)
        else:
            idx[t] = (idx[t - 1] + 1) % T
    return idx


def whites_reality_check(perf_matrix: np.ndarray, avg_block: float = 10.0,
                         n_boot: int = 1000, seed: int = 0) -> dict:
    """White's Reality Check: 「最良戦略の優位はデータスヌーピングの産物か」を検定。

    perf_matrix: shape (T, N)。各列 = 戦略kのベンチ超過パフォーマンス（例: 超過リターン）。
      絶対リターンで見たいならベンチ=0（超過=リターンそのもの）。
    帰無仮説: すべての戦略の期待超過性能 ≤ 0（本物の優位はない）。
    返り値: {"p_value": ..., "best_strategy": ..., "statistic": ...}
      p値が小さいほど「最良戦略の優位は本物」。
    """
    F = np.asarray(perf_matrix, float)
    T, N = F.shape
    rng = np.random.default_rng(seed)
    fbar = F.mean(axis=0)                        # 各戦略の平均超過性能
    V = np.sqrt(T) * np.nanmax(fbar)             # 観測統計量（最良戦略）

    count = 0
    for _ in range(n_boot):
        bidx = _stationary_bootstrap_indices(T, avg_block, rng)
        fbar_b = F[bidx].mean(axis=0)
        V_b = np.sqrt(T) * np.nanmax(fbar_b - fbar)   # 中心化（帰無分布）
        if V_b >= V:
            count += 1
    p = (count + 1) / (n_boot + 1)
    return {
        "p_value": float(p),
        "statistic": float(V),
        "best_strategy": int(np.nanargmax(fbar)),
        "n_strategies": N,
    }
