"""ユニバースの価格・出来高パネル（日付×銘柄）を構築する。

TOPIX500の正確な構成銘柄は無料では取れないため、流動性の高い大型株
25銘柄を**TOPIXの代理ユニバース**として用いる（本物のTOPIX500ではない点に注意）。
各銘柄はYahoo Finance日足をCSVキャッシュする。
"""
import os

import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

# TOPIX大型株の代理ユニバース（流動性の高い25銘柄。正式なTOPIX500ではない）
UNIVERSE = [
    "7203.T", "6758.T", "9984.T", "6861.T", "8306.T",
    "9432.T", "6098.T", "8035.T", "4063.T", "9433.T",
    "8058.T", "6501.T", "7974.T", "6902.T", "8316.T",
    "6367.T", "9983.T", "7267.T", "8031.T", "6981.T",
    "8766.T", "7741.T", "4502.T", "8001.T", "9020.T",
]

# ベンチマーク（TOPIX連動ETF）
BENCHMARK = "1306.T"


def _sanitize(close: pd.Series) -> pd.Series:
    """1日だけの異常値（データグリッチ）を除去する。

    近傍5日メディアンから±40%以上外れた値は誤値とみなしNaN→線形補間する。
    これは過去データの品質管理であり、売買判断ではない（先読みではない）。
    大型株/ETFで1日60%超の乖離はほぼ確実にデータエラー。
    """
    med = close.rolling(5, center=True, min_periods=3).median()
    ratio = close / med
    bad = (ratio < 0.6) | (ratio > 1.6)
    if bad.any():
        close = close.mask(bad).interpolate(limit_direction="both")
    return close


def _fetch_one(symbol: str, range_: str, use_cache: bool) -> pd.DataFrame:
    safe = symbol.replace("^", "_").replace("=", "_")
    path = os.path.join(CACHE_DIR, f"{safe}_{range_}.csv")
    if use_cache and os.path.exists(path):
        return pd.read_csv(path, parse_dates=["date"], index_col="date")

    resp = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": "1d", "includeAdjustedClose": "true"},
        headers=_HEADERS,
        timeout=25,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    ts = result.get("timestamp") or []
    q = result["indicators"]["quote"][0]
    # 分割・配当調整済みの adjclose を close として使う（未調整だと分割日に
    # 偽の±90%リターンが混入する）。無ければ生closeにフォールバック。
    adj = result["indicators"].get("adjclose")
    close_vals = adj[0]["adjclose"] if adj else q.get("close")
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(ts, unit="s", utc=True)
            .tz_convert("Asia/Tokyo")
            .normalize()
            .tz_localize(None),
            "close": close_vals,
            "volume": q.get("volume"),
        }
    )
    df = (
        df.dropna(subset=["close"])
        .drop_duplicates("date", keep="last")
        .set_index("date")
        .sort_index()
    )
    df["close"] = _sanitize(df["close"])
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(path)
    return df


def build_panel(range_: str = "5y", use_cache: bool = True):
    """戻り値: (close, volume) の2つのDataFrame（index=日付, columns=銘柄）。"""
    closes, vols = {}, {}
    for sym in UNIVERSE:
        try:
            df = _fetch_one(sym, range_, use_cache)
        except Exception as e:  # noqa: BLE001
            print(f"  取得失敗 {sym}: {e}")
            continue
        closes[sym] = df["close"]
        vols[sym] = df["volume"]
    close = pd.DataFrame(closes).sort_index()
    volume = pd.DataFrame(vols).reindex(close.index)
    return close, volume


def benchmark_series(range_: str = "5y", use_cache: bool = True) -> pd.Series:
    return _fetch_one(BENCHMARK, range_, use_cache)["close"].rename("benchmark")
