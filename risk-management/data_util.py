"""価格・出来高パネルの取得（Yahoo Finance・adjclose・分割/配当調整済み）。

リスク管理フレームワークのデモ用。他ディレクトリと独立に動くよう自己完結。
"""
import pandas as pd
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_one(symbol: str, range_: str = "2y") -> pd.DataFrame:
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
         "close": close, "volume": ind["quote"][0]["volume"]}
    ).dropna(subset=["close"]).drop_duplicates("date").set_index("date").sort_index()
    return df


def build_panel(symbols: list, range_: str = "2y"):
    """戻り値: (close, volume) DataFrame（index=日付, columns=銘柄）。"""
    closes, vols = {}, {}
    for s in symbols:
        try:
            df = fetch_one(s, range_)
            closes[s], vols[s] = df["close"], df["volume"]
        except Exception as e:  # noqa: BLE001
            print(f"  取得失敗 {s}: {e}")
    close = pd.DataFrame(closes).sort_index()
    return close, pd.DataFrame(vols).reindex(close.index)
