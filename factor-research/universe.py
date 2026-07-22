"""2. 投資ユニバース ―― 対象銘柄を明確な基準で定義し、判定過程を記録する。

流動性・時価総額・データ品質・コーポレートアクションの反映状況を基準に
候補銘柄をスクリーニングし、**どの銘柄がなぜ採用/除外されたか**を
ユニバース構築ログとして残す（再現性の土台）。
"""
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import requests

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

# 候補ユニバース（大型〜中型の代理銘柄群。実際のTOPIX500等の代替）
CANDIDATES = [
    "7203.T", "6758.T", "9984.T", "6861.T", "8306.T", "9432.T", "6098.T",
    "8035.T", "4063.T", "9433.T", "8058.T", "6501.T", "7974.T", "6902.T",
    "8316.T", "6367.T", "9983.T", "7267.T", "8031.T", "6981.T", "8766.T",
    "7741.T", "4502.T", "8001.T", "9020.T", "3382.T", "8267.T", "9022.T",
    "8411.T", "2503.T",
]


@dataclass
class UniverseCriteria:
    min_avg_dollar_volume: float = 3e8    # 平均売買代金の下限（円）
    min_history_days: int = 500            # 最低必要な取得済み営業日数（上場期間の代理）
    max_missing_ratio: float = 0.02        # 許容する欠損率
    min_price: float = 100.0                # 極端な低位株の除外


def _sanitize(close: pd.Series) -> pd.Series:
    med = close.rolling(5, center=True, min_periods=3).median()
    ratio = close / med
    bad = (ratio < 0.6) | (ratio > 1.6)
    if bad.any():
        close = close.mask(bad).interpolate(limit_direction="both")
    return close


def fetch_one(symbol: str, range_: str = "3y") -> pd.DataFrame:
    r = requests.get(
        f"{CHART}/{symbol}",
        params={"range": range_, "interval": "1d", "includeAdjustedClose": "true"},
        headers=_HEADERS, timeout=25,
    ).json()
    res = r["chart"]["result"][0]
    ind = res["indicators"]
    close = ind["adjclose"][0]["adjclose"] if ind.get("adjclose") else ind["quote"][0]["close"]
    df = pd.DataFrame(
        {"date": pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_localize(None),
         "close": close, "volume": ind["quote"][0]["volume"]}
    ).dropna(subset=["close"]).drop_duplicates("date").set_index("date").sort_index()
    df["close"] = _sanitize(df["close"])
    return df


def build_universe(candidates: list = None, criteria: UniverseCriteria = None,
                   range_: str = "3y") -> dict:
    """候補銘柄を基準に照らして判定し、採用銘柄・除外銘柄と理由（構築ログ）を返す。"""
    candidates = candidates or CANDIDATES
    criteria = criteria or UniverseCriteria()

    accepted, rejected, raw_data = [], [], {}
    for sym in candidates:
        try:
            df = fetch_one(sym, range_)
        except Exception as e:  # noqa: BLE001
            rejected.append({"symbol": sym, "reason": f"取得失敗: {e}"})
            continue

        n_days = len(df)
        avg_dollar_vol = float((df["close"] * df["volume"]).mean())
        missing_ratio = float(df["close"].isna().mean())
        last_price = float(df["close"].iloc[-1])

        reasons = []
        if n_days < criteria.min_history_days:
            reasons.append(f"取得日数不足({n_days}<{criteria.min_history_days})")
        if avg_dollar_vol < criteria.min_avg_dollar_volume:
            reasons.append(f"流動性不足(平均売買代金{avg_dollar_vol/1e8:.1f}億円)")
        if missing_ratio > criteria.max_missing_ratio:
            reasons.append(f"欠損率超過({missing_ratio*100:.1f}%)")
        if last_price < criteria.min_price:
            reasons.append(f"低位株(株価{last_price:.0f}円)")

        record = {
            "symbol": sym, "n_days": n_days, "avg_dollar_volume_oku": avg_dollar_vol / 1e8,
            "missing_ratio": missing_ratio, "last_price": last_price,
        }
        if reasons:
            record["reason"] = "; ".join(reasons)
            rejected.append(record)
        else:
            accepted.append(record)
            raw_data[sym] = df
        time.sleep(0.02)

    return {
        "criteria": criteria, "accepted": accepted, "rejected": rejected,
        "raw_data": raw_data,
        "acceptance_rate": len(accepted) / len(candidates) if candidates else np.nan,
    }


def format_universe_log(result: dict) -> str:
    lines = ["=== ユニバース構築ログ ===", f"候補数: {len(result['accepted']) + len(result['rejected'])}"]
    lines.append(f"採用: {len(result['accepted'])}銘柄  除外: {len(result['rejected'])}銘柄  "
                 f"採用率: {result['acceptance_rate']*100:.0f}%")
    lines.append("\n除外銘柄と理由:")
    for r in result["rejected"]:
        lines.append(f"  {r['symbol']}: {r.get('reason', '不明')}")
    return "\n".join(lines)
