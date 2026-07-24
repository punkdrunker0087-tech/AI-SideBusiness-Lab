"""グレアム・リンチ・オニールの各戦略で共通に使うファンダメンタル・スナップショット取得。

⚠️ Yahoo Financeの無料quoteSummary APIは、貸借対照表の明細（流動資産・
流動負債等）を返さない（`balanceSheetHistory`は日付のみでライン
アイテムが空）ことを実装時に確認した。そのため**Grahamの正式なNCAV
（正味流動資産価値）は計算できない**。本シリーズでは、取得可能な
フィールドで代理指標を構築し、その旨を常に明記する。
"""
import time

import numpy as np
import pandas as pd
import requests

_HEADERS = {"User-Agent": "Mozilla/5.0"}
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


def fetch(symbols: list) -> pd.DataFrame:
    s, crumb = _new_session()
    rows = {}
    for sym in symbols:
        try:
            r = s.get(_QS.format(sym),
                     params={"modules": "financialData,defaultKeyStatistics,summaryDetail,price",
                            "crumb": crumb}, timeout=15).json()
            res = r["quoteSummary"]["result"][0]
            fd = res.get("financialData", {})
            ks = res.get("defaultKeyStatistics", {})
            sd = res.get("summaryDetail", {})
            price = res.get("price", {})
            rows[sym] = {
                "trailing_pe": _raw(sd, "trailingPE"),
                "price_to_book": _raw(ks, "priceToBook"),
                "trailing_eps": _raw(ks, "trailingEps"),
                "debt_to_equity": _raw(fd, "debtToEquity"),
                "roe": _raw(fd, "returnOnEquity"),
                "earnings_growth": _raw(fd, "earningsGrowth"),
                "held_pct_institutions": _raw(ks, "heldPercentInstitutions"),
                "market_cap": _raw(price, "marketCap"),
                "gross_margin": _raw(fd, "grossMargins"),
            }
            time.sleep(0.05)
        except Exception:  # noqa: BLE001
            rows[sym] = {k: np.nan for k in [
                "trailing_pe", "price_to_book", "trailing_eps", "debt_to_equity",
                "roe", "earnings_growth", "held_pct_institutions",
                "market_cap", "gross_margin"]}
    return pd.DataFrame(rows).T.astype(float)
