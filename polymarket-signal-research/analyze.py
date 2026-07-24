"""2本の時系列(Polymarket確率 と 金融商品価格)の関係を分析する。

中心的な問い: 「Polymarketの確率変化は、金融商品の値動きに *先行* するか?」

- 両系列を共通の時間グリッド(既定は1時間)に揃える
- 変化量を計算する
  - Polymarket: 確率の差分 (Δprob)
  - 金融商品:   対数リターン (log return)
- ラグ別の相互相関を計算する
  corr( Δprob[t], return[t + k] )  を k = -N..N で走査する
    * k > 0 で相関が最大 → Polymarketが金融商品に *先行* (=予測力の候補)
    * k = 0            → 同時
    * k < 0            → 金融商品がPolymarketに先行
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


def _to_series(history: list, name: str) -> pd.Series:
    """[{"t":unix,"p":val}] を pandas Series(時刻index)に変換する。"""
    if not history:
        return pd.Series(dtype=float, name=name)
    df = pd.DataFrame(history)
    df["t"] = pd.to_datetime(df["t"], unit="s", utc=True)
    s = df.set_index("t")["p"].rename(name)
    return s[~s.index.duplicated(keep="last")].sort_index()


def align(poly_history: list, market_history: list, freq: str = "1h") -> pd.DataFrame:
    """両系列を共通グリッドに揃えたDataFrameを返す(列: prob, price)。"""
    prob = _to_series(poly_history, "prob")
    price = _to_series(market_history, "price")
    if prob.empty or price.empty:
        return pd.DataFrame(columns=["prob", "price"])
    # それぞれをグリッドへリサンプル(直近値で前方補完)
    grid_start = max(prob.index.min(), price.index.min())
    grid_end = min(prob.index.max(), price.index.max())
    if grid_start >= grid_end:
        return pd.DataFrame(columns=["prob", "price"])
    grid = pd.date_range(grid_start, grid_end, freq=freq)
    prob_g = prob.reindex(prob.index.union(grid)).ffill().reindex(grid)
    price_g = price.reindex(price.index.union(grid)).ffill().reindex(grid)
    df = pd.concat([prob_g, price_g], axis=1).dropna()
    return df


@dataclass
class LeadLagResult:
    n_points: int
    best_lag: int          # 金融商品側をずらすラグ(正=Polymarketが先行)
    best_corr: float
    corr_at_zero: float
    lag_table: pd.DataFrame  # 列: lag, corr


def lead_lag(df: pd.DataFrame, max_lag: int = 12) -> LeadLagResult:
    """整列済みDataFrameから、ラグ別相互相関を計算する。"""
    if len(df) < max_lag * 2 + 3:
        raise ValueError(
            f"データ点が不足しています(必要>={max_lag*2+3}, 実際={len(df)})。"
            " 収集期間を延ばすか、fidelity/intervalを細かくしてください。"
        )
    d_prob = df["prob"].diff()
    ret = np.log(df["price"]).diff()

    rows = []
    for k in range(-max_lag, max_lag + 1):
        # k>0 のとき: 今日のΔprob と k時間 *後* のリターンの相関
        shifted_ret = ret.shift(-k)
        pair = pd.concat([d_prob, shifted_ret], axis=1).dropna()
        if len(pair) < 3:
            corr = np.nan
        else:
            corr = pair.iloc[:, 0].corr(pair.iloc[:, 1])
        rows.append({"lag": k, "corr": corr})

    lag_table = pd.DataFrame(rows)
    valid = lag_table.dropna()
    best = valid.loc[valid["corr"].abs().idxmax()]
    corr_zero = float(lag_table.loc[lag_table["lag"] == 0, "corr"].iloc[0])
    return LeadLagResult(
        n_points=len(df),
        best_lag=int(best["lag"]),
        best_corr=float(best["corr"]),
        corr_at_zero=corr_zero,
        lag_table=lag_table,
    )


def _corr_at_lag(a: np.ndarray, b: np.ndarray, k: int) -> float:
    """a[t] と b[t+k] のPearson相関。numpy実装(並べ替え検定の高速化用)。"""
    if k > 0:
        x, y = a[: len(a) - k], b[k:]
    elif k < 0:
        x, y = a[-k:], b[: len(b) + k]
    else:
        x, y = a, b
    mask = ~(np.isnan(x) | np.isnan(y))
    if mask.sum() < 3:
        return np.nan
    x, y = x[mask], y[mask]
    if x.std() == 0 or y.std() == 0:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def _best_lag_corr(a: np.ndarray, b: np.ndarray, max_lag: int):
    """全ラグの中で|相関|が最大のもの(lag, corr)を返す。"""
    best_k, best_c = 0, 0.0
    for k in range(-max_lag, max_lag + 1):
        c = _corr_at_lag(a, b, k)
        if not np.isnan(c) and abs(c) > abs(best_c):
            best_k, best_c = k, c
    return best_k, best_c


def permutation_pvalue(
    df: pd.DataFrame, max_lag: int = 12, n_perm: int = 300, seed: int = 0
):
    """並べ替え検定でp値を求める。

    「Polymarketの確率変化と金融商品リターンに *本当は何の関係もない* 場合、
    今回観測した『全ラグ中の最大相関』がどれくらいの頻度で偶然出るか」を測る。

    Polymarketの確率変化(Δprob)をランダムに並べ替えて関係を壊し、同じ
    「最大相関」統計量を計算し直す。これをn_perm回繰り返し、観測値以上の
    強さが偶然出た割合をp値とする。

    - 全ラグの中の最大を統計量にしているため、複数ラグを試すことによる
      「偽陽性の底上げ」も検定に織り込まれている。
    - 戻り値: (観測された最大相関, p値)
    """
    d_prob = df["prob"].diff().to_numpy()
    ret = np.log(df["price"]).diff().to_numpy()
    _, obs = _best_lag_corr(d_prob, ret, max_lag)
    obs_abs = abs(obs)

    finite_idx = np.where(~np.isnan(d_prob))[0]
    vals = d_prob[finite_idx].copy()
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_perm):
        perm = d_prob.copy()
        perm[finite_idx] = rng.permutation(vals)
        _, c = _best_lag_corr(perm, ret, max_lag)
        if abs(c) >= obs_abs:
            hits += 1
    pval = (hits + 1) / (n_perm + 1)  # +1補正(観測値自身を含める)
    return obs, pval


def interpret(result: LeadLagResult, unit_hours: int = 1) -> str:
    """結果を人間向けの短い解釈文にする(断定はしない)。"""
    lag_h = result.best_lag * unit_hours
    strength = abs(result.best_corr)
    if strength < 0.1:
        band = "ほぼ無相関(予測力の証拠なし)"
    elif strength < 0.3:
        band = "弱い相関"
    elif strength < 0.5:
        band = "中程度の相関"
    else:
        band = "強い相関(ただし過学習・偶然の可能性を要検証)"

    if result.best_lag > 0:
        direction = (
            f"Polymarketの確率変化が金融商品より約{lag_h}時間 *先行* している可能性"
        )
    elif result.best_lag < 0:
        direction = (
            f"金融商品がPolymarketより約{abs(lag_h)}時間先行している"
            "(=Polymarketに予測の優位はない)"
        )
    else:
        direction = "両者は同時に動いている(先行関係なし)"

    return (
        f"データ点: {result.n_points} / "
        f"最大相関ラグ: {result.best_lag}({lag_h}時間) / "
        f"相関係数: {result.best_corr:+.3f}({band}) / "
        f"同時刻の相関: {result.corr_at_zero:+.3f}\n"
        f"解釈: {direction}。\n"
        "注意: n=1回の観測・単一市場の結果は偶然でありうる。複数市場・期間で"
        "再現するか、必ず検証すること。相関は因果を意味しない。"
    )
