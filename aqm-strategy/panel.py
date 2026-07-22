"""ユニバースの価格・出来高パネル（日付×銘柄）を構築する。

TOPIX500の正確な構成銘柄は無料では取れないため、**日経225の構成銘柄
（2026年7月時点、日本経済新聞社の公表データに基づく225銘柄）**を
「TOPIX500に近い規模の大型・流動株ユニバース」の代理として用いる
（日経225であり、正式なTOPIX500ではない点に注意。AQM-01-01の課題
「ユニバースが25銘柄では小さすぎる」を受け、25→225銘柄へ拡大した）。
各銘柄はYahoo Finance日足をCSVキャッシュする。
"""
import os

import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

# 日経225構成銘柄（TOPIX500の代理・正式なTOPIX500ではない）。
# 一部の新規上場銘柄はJPXの新形式コード（英数字4桁、例:543A・285A）。
_NIKKEI225_CODES = [
    "9202", "9201", "543A", "7267", "7202", "7261", "7211", "7201", "7270", "7269",
    "7203", "7272", "8304", "8331", "8354", "8306", "8411", "8308", "5831", "8316",
    "8309", "7186", "3407", "4061", "4901", "4452", "3405", "4188", "4183", "4021",
    "6988", "4004", "4063", "4911", "4005", "4043", "4042", "4208", "9433", "9432",
    "9434", "9984", "1721", "1925", "1808", "1963", "1812", "1802", "1928", "1803",
    "1801", "6857", "6770", "7751", "6902", "6954", "6504", "6702", "6501", "6861",
    "285A", "6971", "6920", "6479", "6503", "6981", "6701", "6594", "6645", "6752",
    "6723", "7752", "6963", "7735", "6724", "6753", "6758", "6526", "6976", "6762",
    "8035", "6506", "6841", "9502", "9503", "9501", "1332", "2802", "2502", "2914",
    "2801", "2503", "2269", "2282", "2871", "2002", "2501", "9532", "9531", "5201",
    "5333", "5214", "5233", "5301", "5332", "8750", "8725", "8630", "8795", "8766",
    "9147", "9064", "6113", "6367", "6361", "6305", "7004", "7013", "5631", "6473",
    "6301", "6326", "7011", "6471", "6472", "6103", "6302", "6273", "9107", "9104",
    "9101", "1605", "5714", "5803", "5801", "5711", "5706", "3436", "5802", "5713",
    "8253", "8697", "8591", "7832", "7912", "7911", "7951", "5020", "5019", "4503",
    "4519", "4568", "4523", "4151", "4578", "4506", "4507", "4502", "6146", "7741",
    "4902", "7731", "7733", "4543", "3861", "9022", "9020", "9008", "9009", "9007",
    "9001", "9005", "9021", "8802", "8801", "8830", "8804", "3289", "8267", "9983",
    "3099", "3086", "8252", "7453", "9843", "7532", "3382", "8233", "3092", "5108",
    "5101", "8601", "8604", "6532", "4751", "2432", "4324", "6178", "9766", "4689",
    "4385", "2413", "3659", "7974", "4307", "4661", "4755", "6098", "9735", "3697",
    "9602", "4704", "7012", "5411", "5406", "5401", "3401", "3402", "8001", "8002",
    "8058", "8031", "2768", "8053", "8015",
]
UNIVERSE = [f"{code}.T" for code in _NIKKEI225_CODES]

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
