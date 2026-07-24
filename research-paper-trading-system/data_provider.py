"""データ取得 ―― 収集・タイムスタンプ整合性・欠損検知・品質監視。

自動発注・ブローカー接続は一切行わない。Yahoo Financeの公開chart APIから
価格を取得し、取得のたびにイベントログへ記録する。
"""
import datetime

import numpy as np
import pandas as pd
import requests

import event_log

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def _sanitize(close: pd.Series) -> pd.Series:
    """1日だけの異常値（データグリッチ）を除去する。

    このリポジトリの複数の実装（aqm-strategy・market-data-platform・
    portfolio-optimization）で繰り返し検出されたYahoo側の既知の問題への対処。
    """
    med = close.rolling(5, center=True, min_periods=3).median()
    ratio = close / med
    bad = (ratio < 0.6) | (ratio > 1.6)
    if bad.any():
        close = close.mask(bad).interpolate(limit_direction="both")
    return close


def fetch(symbol: str, range_: str = "2y", run_id: str = None) -> pd.DataFrame:
    """価格を取得し、取得イベントと検証結果をログに残す。"""
    resp = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": "1d", "includeAdjustedClose": "true"},
        headers=_HEADERS, timeout=25,
    )
    resp.raise_for_status()
    res = resp.json()["chart"]["result"][0]
    ind = res["indicators"]
    close = ind["adjclose"][0]["adjclose"] if ind.get("adjclose") else ind["quote"][0]["close"]
    df = pd.DataFrame(
        {"date": pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_localize(None),
         "close": close, "volume": ind["quote"][0]["volume"]}
    ).dropna(subset=["close"]).drop_duplicates("date").set_index("date").sort_index()

    event_log.log_event("data_fetch", {
        "symbol": symbol, "source": "yahoo_finance_chart_api",
        "n_rows": len(df), "range": range_,
        "latest_date": str(df.index[-1].date()) if len(df) else None,
    }, run_id=run_id)

    validation = validate(df, symbol, run_id=run_id)
    df["close"] = _sanitize(df["close"])
    if validation["outliers_detected"] > 0:
        df.attrs["had_outliers_sanitized"] = True

    return df


def validate(df: pd.DataFrame, symbol: str, run_id: str = None) -> dict:
    """タイムスタンプ整合性・欠損・異常値を確認し、検証イベントを記録する。"""
    ret = df["close"].pct_change()
    result = {
        "symbol": symbol,
        "n_rows": len(df),
        "duplicate_timestamps": int(df.index.duplicated().sum()),
        "monotonic": bool(df.index.is_monotonic_increasing),
        "missing_values": int(df["close"].isna().sum()),
        "outliers_detected": int(((ret.abs() > 0.5)).sum()),
        "latency_days": (datetime.datetime.now(datetime.timezone.utc).date()
                        - df.index[-1].date()).days if len(df) else None,
    }
    event_log.log_event("data_validation", result, run_id=run_id)
    return result
