"""価格パネル・セクター取得（Yahoo Finance）。自己完結。"""
import time

import pandas as pd
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

# ペア候補探索用ユニバース: 同一業種内で複数銘柄を含むよう意図的に構成
# （銀行3・自動車2・商社2・通信2・鉄道2・小売2・電機2 等、業種内ペアを作れる構成）
UNIVERSE = [
    "8306.T", "8316.T", "8411.T",   # 銀行: 三菱UFJ・三井住友・みずほ
    "7203.T", "7267.T",             # 自動車: トヨタ・ホンダ
    "8031.T", "8058.T", "8001.T",   # 商社: 三井物産・三菱商事・伊藤忠
    "9432.T", "9433.T",             # 通信: NTT・KDDI
    "9020.T", "9022.T",             # 鉄道: JR東日本・JR東海
    "3382.T", "8267.T",             # 小売: セブン&アイ・イオン
    "6758.T", "6501.T",             # 電機: ソニー・日立
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


_QS = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"


def fetch_sectors(symbols=None) -> pd.Series:
    """銘柄ごとのセクター・業種（同業種ペア探索・複数ペア管理の集中度判定用）。"""
    symbols = symbols or UNIVERSE
    s = requests.Session()
    s.headers.update(_HEADERS)
    s.get("https://fc.yahoo.com", timeout=10)
    crumb = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10).text
    rows = {}
    for sym in symbols:
        try:
            r = s.get(_QS.format(sym), params={"modules": "assetProfile", "crumb": crumb},
                     timeout=15).json()
            ap = r["quoteSummary"]["result"][0].get("assetProfile", {})
            rows[sym] = ap.get("industry", "不明")
            time.sleep(0.05)
        except Exception:  # noqa: BLE001
            rows[sym] = "不明"
    return pd.Series(rows, name="industry")
