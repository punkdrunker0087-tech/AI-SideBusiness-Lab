"""日本株・ETF・指数の日足データを取得する（Yahoo Finance公開chart API）。

バックテストは無料の過去データで行い、実際の発注は楽天証券RSSで行う想定。
取得したデータは data/ にCSVキャッシュする（再取得を避け、再現性も担保）。

シンボル例:
  7203.T  トヨタ自動車 / 6758.T ソニーG / 9984.T ソフトバンクG
  1321.T  日経225連動ETF / 1570.T 日経レバETF / ^N225 日経225指数
"""
import os

import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def _cache_path(symbol: str, range_: str, interval: str) -> str:
    safe = symbol.replace("^", "_").replace("=", "_")
    return os.path.join(CACHE_DIR, f"{safe}_{range_}_{interval}.csv")


def fetch(
    symbol: str,
    range_: str = "2y",
    interval: str = "1d",
    use_cache: bool = True,
) -> pd.DataFrame:
    """OHLCV日足を取得する。戻り値のindexは日付（Asia/Tokyo・00:00に正規化）。"""
    path = _cache_path(symbol, range_, interval)
    if use_cache and os.path.exists(path):
        return pd.read_csv(path, parse_dates=["date"], index_col="date")

    resp = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": interval},
        headers=_HEADERS,
        timeout=25,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    ts = result.get("timestamp") or []
    q = result["indicators"]["quote"][0]
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(ts, unit="s", utc=True)
            .tz_convert("Asia/Tokyo")
            .normalize()
            .tz_localize(None),
            "open": q.get("open"),
            "high": q.get("high"),
            "low": q.get("low"),
            "close": q.get("close"),
            "volume": q.get("volume"),
        }
    )
    df = (
        df.dropna(subset=["close"])
        .drop_duplicates("date", keep="last")
        .set_index("date")
        .sort_index()
    )
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(path)
    return df
