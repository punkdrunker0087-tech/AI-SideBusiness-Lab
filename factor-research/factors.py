"""3. ファクター構築 ―― バリュー・モメンタム・クオリティ・サイズ。

将来情報混入を避けるため、価格ベース(モメンタム)は`rolling`/`shift`のみで
構築する。バリュー・クオリティ・サイズはYahoo財務スナップショット
（現在値のみ・登録不要）に依拠し、**過去への一律適用は先読みバイアスになる
ことを明示**する（`../aqm-strategy/quality.py`・`../multifactor-investing/`
と同じ制約）。
"""
import time

import numpy as np
import pandas as pd
import requests

_HEADERS = {"User-Agent": "Mozilla/5.0"}
_QS = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"


def momentum(close: pd.DataFrame, lookback: int = 120) -> pd.DataFrame:
    return close / close.rolling(lookback).mean() - 1


def cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, np.nan), axis=0)


def _new_session():
    s = requests.Session()
    s.headers.update(_HEADERS)
    s.get("https://fc.yahoo.com", timeout=10)
    crumb = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10).text
    return s, crumb


def _raw(d, key):
    v = d.get(key)
    return v.get("raw") if isinstance(v, dict) else v


def fetch_snapshot_fundamentals(symbols: list) -> pd.DataFrame:
    """Value(PER/PBR)・Quality(ROE/粗利率)・Size(時価総額)の現在スナップショット。"""
    s, crumb = _new_session()
    rows = {}
    for sym in symbols:
        try:
            r = s.get(_QS.format(sym),
                     params={"modules": "financialData,defaultKeyStatistics,price,summaryDetail",
                            "crumb": crumb}, timeout=15).json()
            res = r["quoteSummary"]["result"][0]
            fd, ks = res.get("financialData", {}), res.get("defaultKeyStatistics", {})
            price, sd = res.get("price", {}), res.get("summaryDetail", {})
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


def _robust_z(s: pd.Series) -> pd.Series:
    s = s.clip(s.quantile(0.02), s.quantile(0.98))
    s = s.fillna(s.median())
    sd = s.std()
    return (s - s.mean()) / sd if sd else pd.Series(0.0, index=s.index)


def build_snapshot_factors(fundamentals: pd.DataFrame) -> pd.DataFrame:
    """Value/Quality/Sizeの合成Zスコア（銘柄index、ライブ断面専用）。"""
    value = (_robust_z(1.0 / fundamentals["trailing_pe"].replace(0, np.nan))
            + _robust_z(1.0 / fundamentals["price_to_book"].replace(0, np.nan))) / 2
    quality = (_robust_z(fundamentals["roe"]) + _robust_z(fundamentals["gross_margin"])) / 2
    size = _robust_z(-np.log(fundamentals["market_cap"].replace(0, np.nan)))
    return pd.DataFrame({"value": value, "quality": quality, "size": size})
