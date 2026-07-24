"""価格・出来高パネル取得（Yahoo Finance・adjclose）。自己完結。"""
import pandas as pd
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

UNIVERSE = [
    "7203.T", "6758.T", "9984.T", "6861.T", "8306.T", "9432.T", "6098.T",
    "8035.T", "4063.T", "9433.T", "8058.T", "6501.T", "7974.T", "6902.T",
    "8316.T", "6367.T", "9983.T", "7267.T", "8031.T", "6981.T", "8766.T",
    "7741.T", "4502.T", "8001.T", "9020.T",
]


def fetch_one(symbol: str, range_: str = "5y") -> pd.DataFrame:
    r = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": "1d", "includeAdjustedClose": "true"},
        headers=_HEADERS, timeout=25,
    ).json()
    res = r["chart"]["result"][0]
    ind = res["indicators"]
    close = ind["adjclose"][0]["adjclose"] if ind.get("adjclose") else ind["quote"][0]["close"]
    return pd.DataFrame(
        {"date": pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_localize(None),
         "close": close, "volume": ind["quote"][0]["volume"]}
    ).dropna(subset=["close"]).drop_duplicates("date").set_index("date").sort_index()


def build_panel(symbols=None, range_: str = "5y"):
    symbols = symbols or UNIVERSE
    closes, vols = {}, {}
    for s in symbols:
        try:
            df = fetch_one(s, range_)
            closes[s], vols[s] = df["close"], df["volume"]
        except Exception as e:  # noqa: BLE001
            print(f"  取得失敗 {s}: {e}")
    close = pd.DataFrame(closes).sort_index()
    return close, pd.DataFrame(vols).reindex(close.index)
