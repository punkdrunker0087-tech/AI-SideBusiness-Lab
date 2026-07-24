"""マルチアセット価格パネル取得（Yahoo Finance・adjclose）。自己完結。

日本上場ETFで6資産クラスを代表させる:
  国内株・海外株・国内債・海外債・金・REIT
"""
import pandas as pd
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

ASSETS = {
    "1306.T": "国内株(TOPIX)",
    "1657.T": "海外株(MSCI Kokusai)",
    "2510.T": "国内債(NOMURA-BPI)",
    "1656.T": "海外債(米国7-10年国債)",
    "1540.T": "金(現物)",
    "1343.T": "REIT(東証REIT指数)",
}


def _sanitize(close: pd.Series) -> pd.Series:
    """1日だけの異常値（データグリッチ）を除去する。

    近傍5日メディアンから±40%以上外れた値は誤値とみなしNaN→線形補間する。
    Yahoo Finance の日本上場ETF系列で実際に観測される問題（例: 1306.Tで
    2日間だけ約1/10の誤値が入る）への対処（`../aqm-strategy/panel.py`と同じ方針）。
    """
    med = close.rolling(5, center=True, min_periods=3).median()
    ratio = close / med
    bad = (ratio < 0.6) | (ratio > 1.6)
    if bad.any():
        close = close.mask(bad).interpolate(limit_direction="both")
    return close


def fetch_one(symbol: str, range_: str = "5y") -> pd.DataFrame:
    r = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": "1d", "includeAdjustedClose": "true"},
        headers=_HEADERS, timeout=25,
    ).json()
    res = r["chart"]["result"][0]
    ind = res["indicators"]
    close = ind["adjclose"][0]["adjclose"] if ind.get("adjclose") else ind["quote"][0]["close"]
    df = pd.DataFrame(
        {"date": pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_localize(None),
         "close": close}
    ).dropna(subset=["close"]).drop_duplicates("date").set_index("date").sort_index()
    df["close"] = _sanitize(df["close"])
    return df


def build_panel(range_: str = "5y") -> pd.DataFrame:
    """戻り値: 列=資産コード, 値=調整後終値のDataFrame。"""
    closes = {}
    for sym in ASSETS:
        try:
            closes[sym] = fetch_one(sym, range_)["close"]
        except Exception as e:  # noqa: BLE001
            print(f"  取得失敗 {sym}: {e}")
    return pd.DataFrame(closes).sort_index().dropna()
