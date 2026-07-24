"""為替（ドル円）感応度ファクター ―― 「銘柄ごとの円安・円高への反応度」を横断比較する。

## 背景・設計思想
Momentum/LowVol/Liquidityは価格・出来高の統計的パターンのみを見ており、
「なぜ動いたか」（為替・金利・政策等のマクロ要因）は一切考慮しない。
ドル円レート自体は全銘柄に共通の値なので、そのままクロスセクショナル
Zスコアの対象にはできない（横断的な差を生まない）。

そこで、**銘柄ごとのドル円変化に対する感応度（FXベータ）**を計算し、
それを横断的にランク付けするファクターとして構築する。輸出比率の高い
銘柄は円安でFXベータが正に高く出るはず、内需銘柄は感応度が低いはず、
という仮説を検証する。

  FX_beta_i(t) = Cov(R_i, R_fx, 過去window日) / Var(R_fx, 過去window日)

R_fx はドル円の変化率（プラス=円安、マイナス=円高）。全期間ローリング
計算のため先読みはない。
"""
import os

import numpy as np
import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
USDJPY_TICKER = "JPY=X"


def fetch_usdjpy(range_: str = "15y", use_cache: bool = True) -> pd.Series:
    path = os.path.join(CACHE_DIR, f"usdjpy_{range_}.csv")
    if use_cache and os.path.exists(path):
        return pd.read_csv(path, parse_dates=["date"], index_col="date")["close"]

    resp = requests.get(f"{CHART}/{USDJPY_TICKER}",
                        params={"range": range_, "interval": "1d"},
                        headers=_HEADERS, timeout=25)
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    ts = result["timestamp"]
    close = result["indicators"]["quote"][0]["close"]
    df = pd.DataFrame({
        "date": pd.to_datetime(ts, unit="s", utc=True).tz_convert("Asia/Tokyo")
        .normalize().tz_localize(None),
        "close": close,
    })
    df = (df.dropna(subset=["close"]).drop_duplicates("date", keep="last")
         .set_index("date").sort_index())
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(path)
    return df["close"]


def rolling_fx_beta(stock_returns: pd.DataFrame, fx_returns: pd.Series,
                    window: int = 252) -> pd.DataFrame:
    """各銘柄・各日のローリングFXベータ（過去window日、先読みなし）。"""
    fx = fx_returns.reindex(stock_returns.index)
    fx_var = fx.rolling(window).var()
    betas = {}
    for col in stock_returns.columns:
        cov = stock_returns[col].rolling(window).cov(fx)
        betas[col] = cov / fx_var
    return pd.DataFrame(betas)


def fx_zscore_factor(close: pd.DataFrame, fx_close: pd.Series, window: int = 252) -> pd.DataFrame:
    """FXベータを計算し、日次クロスセクショナルZスコアにする（高いほど円安に強い）。"""
    import factors  # 既存のzscore_crossを再利用
    stock_ret = close.pct_change()
    fx_ret = fx_close.reindex(close.index).ffill().pct_change()
    beta = rolling_fx_beta(stock_ret, fx_ret, window)
    return factors.zscore_cross(beta)
