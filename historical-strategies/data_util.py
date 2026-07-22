"""OHLC価格パネル取得（Yahoo Finance・adjclose補正）。自己完結。

タートルズのシステムはTrue Range（高値・安値・前日終値）が必要なため、
他フレームワークと異なり終値だけでなくOHLC全体を取得する。
"""
import pandas as pd
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
    """1日だけの異常値（データグリッチ）を除去する（このリポジトリ複数箇所で
    検出済みのYahoo側の既知の問題への対処）。"""
    med = df["close"].rolling(5, center=True, min_periods=3).median()
    ratio = df["close"] / med
    bad = (ratio < 0.6) | (ratio > 1.6)
    if bad.any():
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].mask(bad).interpolate(limit_direction="both")
    return df


def fetch_ohlc(symbol: str, range_: str = "5y") -> pd.DataFrame:
    r = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": "1d", "includeAdjustedClose": "true"},
        headers=_HEADERS, timeout=25,
    ).json()
    res = r["chart"]["result"][0]
    ind = res["indicators"]
    q = ind["quote"][0]
    adj = ind.get("adjclose")
    # 分割調整: adjcloseとcloseの比率を全OHLCに適用する
    close_raw = pd.Series(q["close"])
    close_adj = pd.Series(adj[0]["adjclose"]) if adj else close_raw
    adj_factor = (close_adj / close_raw).fillna(1.0)

    df = pd.DataFrame({
        "date": pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_localize(None),
        "open": pd.Series(q["open"]) * adj_factor,
        "high": pd.Series(q["high"]) * adj_factor,
        "low": pd.Series(q["low"]) * adj_factor,
        "close": close_adj,
        "volume": q["volume"],
    }).dropna(subset=["close"]).drop_duplicates("date").set_index("date").sort_index()
    return _sanitize(df)
