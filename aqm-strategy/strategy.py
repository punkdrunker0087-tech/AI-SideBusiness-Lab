"""合成スコア → ロング/ショート構築 → バックテスト。

market-neutral（ドルニュートラル）のクロスセクショナル・ファクター戦略として
実装する。各リバランス日にスコア上位をロング・下位をショートし、
逆ボラティリティで各レッグを配分、Gross≈150%・Net≈0に保つ。

Qualityが取得できないため、その重み0.25を残り3ファクターへ比率保持で
再配分する（MEMO.md「Quality欠落の扱い」参照）。
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

import factors

# 元の重み: M=0.40, Q=0.25, σ=−0.20, L=0.15
# Q欠落 → M:σ:L の比率を保ったまま |重み|和=1 に正規化
_RAW = {"M": 0.40, "sigma": -0.20, "L": 0.15}
_ABS_SUM = sum(abs(w) for w in _RAW.values())  # 0.75
WEIGHTS = {k: w / _ABS_SUM for k, w in _RAW.items()}  # M=0.533, σ=-0.267, L=0.200


# Quality を含む本来の重み（ライブ・ランキング用）
FULL_WEIGHTS = {"M": 0.40, "Q": 0.25, "sigma": -0.20, "L": 0.15}


def composite_score(
    close: pd.DataFrame, volume: pd.DataFrame, static_quality_z: pd.Series = None
) -> pd.DataFrame:
    """各日・各銘柄の合成スコア（高いほどロング向き）。

    static_quality_z=None: Quality抜きの3ファクター版（先読みなし・既定）。
    static_quality_z を渡すと、その現在スナップショットQを全期間に一律適用した
    4ファクター版になる（⚠️ look-ahead bias。上限推定・感度分析専用）。
    """
    zM = factors.zscore_cross(factors.momentum(close))
    zS = factors.zscore_cross(factors.volatility(close))
    zL = factors.zscore_cross(factors.liquidity(close, volume))
    if static_quality_z is None:
        return WEIGHTS["M"] * zM + WEIGHTS["sigma"] * zS + WEIGHTS["L"] * zL

    q = static_quality_z.reindex(close.columns).fillna(0.0)
    qdf = pd.DataFrame(
        np.tile(q.values, (len(close), 1)), index=close.index, columns=close.columns
    )
    w = FULL_WEIGHTS
    return w["M"] * zM + w["sigma"] * zS + w["L"] * zL + w["Q"] * qdf


def live_scores(close: pd.DataFrame, volume: pd.DataFrame, quality_z: pd.Series) -> pd.Series:
    """最新日の 4ファクター合成スコア（銘柄index）。今日の判断に今日のデータを
    使う正当な用途（先読みではない）。quality_z は quality.quality_zscore の出力。"""
    zM = factors.zscore_cross(factors.momentum(close)).iloc[-1]
    zS = factors.zscore_cross(factors.volatility(close)).iloc[-1]
    zL = factors.zscore_cross(factors.liquidity(close, volume)).iloc[-1]
    q = quality_z.reindex(close.columns).fillna(0.0)
    w = FULL_WEIGHTS
    return (w["M"] * zM + w["sigma"] * zS + w["L"] * zL + w["Q"] * q).rename("score")


@dataclass
class BTResult:
    equity: pd.Series
    returns: pd.Series
    weights: pd.DataFrame
    gross: pd.Series
    net: pd.Series


def backtest(
    close: pd.DataFrame,
    score: pd.DataFrame,
    top_q: float = 0.2,
    rebalance: str = "ME",
    leg_gross: float = 0.75,
    cost_bps: float = 15.0,          # 手数料5 + スリッページ10
    borrow_bps_annual: float = 100.0,  # 空売りコスト（年率）
    min_names: int = 6,
) -> BTResult:
    """ドルニュートラルなロング/ショートのバックテスト。

    top_q: 上位/下位それぞれ何割をロング/ショートするか（例0.2=上下20%）。
    leg_gross: 各レッグの総額（0.75 → Gross≈1.5, Net≈0）。
    """
    ret = close.pct_change()
    vol = factors.volatility(close)

    # リバランス日（月末など。指数内に存在する営業日へスナップ）
    rebal_days = close.resample(rebalance).last().index
    rebal_days = [d for d in rebal_days if d in close.index]

    # リバランス日だけ配分ベクトルを入れ、他はNaN → ffillで前回配分を維持
    weights = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for t in rebal_days:
        s = score.loc[t].dropna()
        if len(s) < min_names:
            continue
        k = max(1, int(len(s) * top_q))
        longs = s.nlargest(k).index
        shorts = s.nsmallest(k).index

        iv = (1.0 / vol.loc[t]).replace([np.inf, -np.inf], np.nan)
        wl = iv[longs].dropna()
        ws = iv[shorts].dropna()
        if wl.empty or ws.empty:
            continue
        wl = wl / wl.sum() * leg_gross
        ws = ws / ws.sum() * leg_gross

        w = pd.Series(0.0, index=close.columns)  # 非選択銘柄は明示的に0
        w[wl.index] = wl.values
        w[ws.index] = -ws.values
        weights.loc[t] = w

    weights = weights.ffill().fillna(0.0)

    held = weights.shift(1).fillna(0.0)
    port_ret = (held * ret).sum(axis=1)

    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    cost = turnover * (cost_bps / 1e4)
    short_notional = held.clip(upper=0).abs().sum(axis=1)
    borrow = short_notional * (borrow_bps_annual / 1e4 / 252)

    net_ret = port_ret - cost - borrow
    equity = (1 + net_ret).cumprod()
    gross = held.abs().sum(axis=1)
    net_exp = held.sum(axis=1)
    return BTResult(equity, net_ret, weights, gross, net_exp)


TRADING_DAYS = 252


def metrics(net_ret: pd.Series, equity: pd.Series, benchmark_ret: pd.Series = None) -> dict:
    n = len(net_ret)
    years = n / TRADING_DAYS if n else np.nan
    total = float(equity.iloc[-1] - 1) if n else np.nan
    cagr = float(equity.iloc[-1] ** (1 / years) - 1) if years and years > 0 else np.nan
    vol = float(net_ret.std() * np.sqrt(TRADING_DAYS)) if n else np.nan
    sharpe = float(net_ret.mean() * TRADING_DAYS / vol) if vol and vol > 0 else np.nan
    downside = net_ret[net_ret < 0].std() * np.sqrt(TRADING_DAYS)
    sortino = float(net_ret.mean() * TRADING_DAYS / downside) if downside and downside > 0 else np.nan
    dd = (equity / equity.cummax() - 1).min()
    max_dd = float(dd) if n else np.nan
    calmar = float(cagr / abs(max_dd)) if max_dd and max_dd < 0 else np.nan
    win = float((net_ret > 0).mean()) if n else np.nan

    out = {
        "total_return": total, "cagr": cagr, "vol": vol, "sharpe": sharpe,
        "sortino": sortino, "max_drawdown": max_dd, "calmar": calmar,
        "win_rate": win, "n_days": n,
    }
    if benchmark_ret is not None:
        aligned = pd.concat([net_ret, benchmark_ret], axis=1).dropna()
        if len(aligned) > 2 and aligned.iloc[:, 1].var() > 0:
            beta = float(np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0, 1]
                         / aligned.iloc[:, 1].var())
            out["beta_vs_bench"] = beta
    return out


def format_metrics(m: dict) -> str:
    def f(v, spec, scale=1.0):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return " — "
        return format(v * scale, spec)

    s = (
        f"総リターン {f(m['total_return'],'+6.1f',100)}%  "
        f"CAGR {f(m['cagr'],'+5.1f',100)}%  "
        f"Sharpe {f(m['sharpe'],'+.2f')}  "
        f"Sortino {f(m['sortino'],'+.2f')}  "
        f"最大DD {f(m['max_drawdown'],'6.1f',100)}%  "
        f"勝率 {f(m['win_rate'],'4.1f',100)}%"
    )
    if "beta_vs_bench" in m:
        s += f"  β {f(m['beta_vs_bench'],'+.2f')}"
    return s
