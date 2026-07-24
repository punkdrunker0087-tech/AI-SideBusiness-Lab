"""価格パネル取得（Yahoo Finance・adjclose）＋ ファンダメンタル・スナップショット
（Yahoo quoteSummary・crumb認証・登録不要）。自己完結。

⚠️ ファンダメンタル値（PER/PBR/ROE/時価総額）は**現在のスナップショット**。
過去バックテストへの一律適用は先読みバイアス（`factors.py` 参照）。
"""
import time

import numpy as np
import pandas as pd
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

# 大型株の代理ユニバース（他ディレクトリと同一の25銘柄。セクターが混在）
UNIVERSE = [
    "7203.T", "6758.T", "9984.T", "6861.T", "8306.T", "9432.T", "6098.T",
    "8035.T", "4063.T", "9433.T", "8058.T", "6501.T", "7974.T", "6902.T",
    "8316.T", "6367.T", "9983.T", "7267.T", "8031.T", "6981.T", "8766.T",
    "7741.T", "4502.T", "8001.T", "9020.T",
]
BENCHMARK = "1306.T"


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


# --- ファンダメンタル・スナップショット（Value/Quality/Size用） ---
_QS = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"


def _new_session():
    s = requests.Session()
    s.headers.update(_HEADERS)
    s.get("https://fc.yahoo.com", timeout=10)
    crumb = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10).text
    return s, crumb


def _raw(d, key):
    v = d.get(key)
    return v.get("raw") if isinstance(v, dict) else v


def fetch_fundamentals(symbols=None) -> pd.DataFrame:
    """PER・PBR・時価総額・ROE・粗利率を銘柄×指標のDataFrameで返す（現在値）。"""
    symbols = symbols or UNIVERSE
    s, crumb = _new_session()
    rows = {}
    for sym in symbols:
        try:
            r = s.get(
                _QS.format(sym),
                params={"modules": "financialData,defaultKeyStatistics,price,summaryDetail",
                        "crumb": crumb},
                timeout=15,
            ).json()
            res = r["quoteSummary"]["result"][0]
            fd = res.get("financialData", {})
            ks = res.get("defaultKeyStatistics", {})
            price = res.get("price", {})
            sd = res.get("summaryDetail", {})
            rows[sym] = {
                "trailing_pe": _raw(sd, "trailingPE"),
                "price_to_book": _raw(ks, "priceToBook"),
                "market_cap": _raw(price, "marketCap"),
                "roe": _raw(fd, "returnOnEquity"),
                "gross_margin": _raw(fd, "grossMargins"),
            }
            time.sleep(0.05)
        except Exception:  # noqa: BLE001
            rows[sym] = {k: np.nan for k in
                        ["trailing_pe", "price_to_book", "market_cap", "roe", "gross_margin"]}
    return pd.DataFrame(rows).T.astype(float)


def fetch_sectors(symbols=None) -> pd.Series:
    """銘柄ごとのセクター（GICS相当）を返す（地域・セクターエクスポージャー用）。"""
    symbols = symbols or UNIVERSE
    s, crumb = _new_session()
    rows = {}
    for sym in symbols:
        try:
            r = s.get(
                _QS.format(sym),
                params={"modules": "assetProfile", "crumb": crumb},
                timeout=15,
            ).json()
            ap = r["quoteSummary"]["result"][0].get("assetProfile", {})
            rows[sym] = ap.get("sector", "不明")
            time.sleep(0.05)
        except Exception:  # noqa: BLE001
            rows[sym] = "不明"
    return pd.Series(rows, name="sector")
