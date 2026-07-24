"""データ取得レイヤー ―― データ提供元からの取得と、取得メタデータの記録。

Yahoo Financeの公開chart APIを例に、以下を必ず記録する:
  - どの提供元から
  - いつ取得したか（取得時刻）
  - どの粒度（日足のみ対応。分足・ティックは同一設計を拡張すれば対応可）
"""
import datetime
from dataclasses import dataclass, field

import pandas as pd
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


@dataclass
class FetchResult:
    symbol: str
    source: str
    granularity: str
    fetched_at: str            # ISO8601 UTC
    raw: pd.DataFrame          # 取得したそのままのOHLCV（未加工）
    license_note: str = "Yahoo Finance 公開API・非商用の学習利用を想定"


def fetch_daily(symbol: str, range_: str = "2y") -> FetchResult:
    """日足OHLCVを取得する。raw/adjcloseの両方を保持し、コーポレートアクション
    検知（`corporate_actions.py`）で使えるようにする。
    """
    resp = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": "1d", "includeAdjustedClose": "true"},
        headers=_HEADERS, timeout=25,
    )
    resp.raise_for_status()
    res = resp.json()["chart"]["result"][0]
    ind = res["indicators"]
    q = ind["quote"][0]
    adj = ind.get("adjclose")

    df = pd.DataFrame({
        "timestamp": res["timestamp"],
        "open": q.get("open"),
        "high": q.get("high"),
        "low": q.get("low"),
        "close": q.get("close"),
        "adjclose": adj[0]["adjclose"] if adj else q.get("close"),
        "volume": q.get("volume"),
    })
    df["date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_localize(None)
    df = df.drop(columns=["timestamp"]).set_index("date").sort_index()

    return FetchResult(
        symbol=symbol, source="yahoo_finance_chart_api", granularity="1d",
        fetched_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        raw=df,
    )
