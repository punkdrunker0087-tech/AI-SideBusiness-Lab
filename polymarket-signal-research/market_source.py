"""日本で合法的に取引できる金融商品の価格時系列を取得するモジュール。

Yahoo Finance の公開chart APIを requests 経由で叩く(curl_cffiを使う
yfinance本体はこの環境のプロキシと相性が悪いため、素のrequestsで実装)。

代表的なシンボル:
- ^N225     : 日経225
- USDJPY=X  : ドル円
- 1570.T    : NEXT FUNDS 日経平均レバレッジ上場投信(楽天証券で取引可能な例)
- ^TPX      : TOPIX
"""
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def price_history(symbol: str, range_: str = "1mo", interval: str = "1h") -> list:
    """Yahoo Finance から価格時系列を取得する。

    戻り値: [{"t": unix_seconds, "p": close_price}, ...]
    range_: "5d" / "1mo" / "3mo" / "6mo" など
    interval: "1h" / "1d" / "60m" など
    """
    resp = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": interval},
        headers=_HEADERS,
        timeout=25,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    closes = result["indicators"]["quote"][0].get("close") or []
    out = []
    for t, p in zip(timestamps, closes):
        if p is None:
            continue
        out.append({"t": int(t), "p": float(p)})
    return out
