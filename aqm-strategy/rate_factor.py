"""金利感応度ファクター ―― 「銘柄ごとの金利変化への反応度」を横断比較する。

FXベータ（`fx_factor.py`）と同じ発想: 金利水準自体は全銘柄共通の値
なので横断比較の材料にならないが、「この銘柄は金利上昇にどれだけ
反応するか」という**銘柄ごとの感応度**は横断的なランキング材料になる。
金融株は金利上昇で恩恵を受けやすく、高配当・ディフェンシブ銘柄は
金利上昇で相対的に不利になりやすい、という仮説を検証する。

⚠️ 日本国債（JGB）そのものの利回り系列はYahoo Financeの無料APIでは
安定して取得できない（`2510.T`等のJGB ETFは2017年以降のデータしかなく、
本シリーズの15年間をカバーしない）。そこで**米国10年国債利回り
（^TNX）**を代用する。米金利は(a)グローバルなリスクセンチメント、
(b)日米金利差を通じたドル円への影響、を介して日本株にも波及するため、
無関係ではないが、**これはFXベータ（ドル円感応度）と高い相関を持つ
可能性がある**（日米金利差が円安・円高の主要因の一つであるため）。
そのため、FXベータとの相関を必ず確認し、単なる「同じ信号の言い換え」
になっていないかを検証する。
"""
import os

import numpy as np
import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
RATE_TICKER = "%5ETNX"  # ^TNX（米10年国債利回り、URLエンコード済み）


def fetch_us10y(range_: str = "15y", use_cache: bool = True) -> pd.Series:
    path = os.path.join(CACHE_DIR, f"us10y_{range_}.csv")
    if use_cache and os.path.exists(path):
        return pd.read_csv(path, parse_dates=["date"], index_col="date")["close"]

    resp = requests.get(f"{CHART}/{RATE_TICKER}",
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


def rolling_rate_beta(stock_returns: pd.DataFrame, rate_changes: pd.Series,
                      window: int = 252) -> pd.DataFrame:
    """各銘柄・各日のローリング金利ベータ（過去window日、先読みなし）。

    rate_changesは利回りの日次変化(差分、%change ではない。利回り自体が
    %表示のため差分を使う)。
    """
    rc = rate_changes.reindex(stock_returns.index)
    rc_var = rc.rolling(window).var()
    betas = {}
    for col in stock_returns.columns:
        cov = stock_returns[col].rolling(window).cov(rc)
        betas[col] = cov / rc_var
    return pd.DataFrame(betas)


def rate_zscore_factor(close: pd.DataFrame, rate_close: pd.Series, window: int = 252) -> pd.DataFrame:
    """金利ベータを計算し、日次クロスセクショナルZスコアにする（高いほど金利上昇に強い）。"""
    import factors  # 既存のzscore_crossを再利用
    stock_ret = close.pct_change()
    rate_chg = rate_close.reindex(close.index).ffill().diff()
    beta = rolling_rate_beta(stock_ret, rate_chg, window)
    return factors.zscore_cross(beta)
