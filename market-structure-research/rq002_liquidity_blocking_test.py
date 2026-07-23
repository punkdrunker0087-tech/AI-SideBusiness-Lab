"""RQ-002の検証: 決算後の価格反応の前倒し(RQ-001のH2b)は、流動性で
条件づけても両群で残るか。

事前登録: research_questions/theme1_price_reaction_speed/
RQ-002_liquidity_blocking.md
RQ-001のパイプライン(compute_ar, run_reaction_speed_pipeline)は
一切変更せずインポートして使う。流動性による層別ロジックのみ新規。
"""
import os

import numpy as np
import pandas as pd

from earnings_reaction_speed_test import (
    AQM_DATA,
    compute_ar,
    load_disclosure_dates,
    load_universe_prices,
    run_reaction_speed_pipeline,
)

LIQ_WINDOW = 60
CAR_LONG = 20


def load_universe_volume():
    vols = {}
    for fn in os.listdir(AQM_DATA):
        if fn.endswith("_15y.csv") and ".T_" in fn:
            code = fn.replace("_15y.csv", "").replace(".T", "")
            df = pd.read_csv(os.path.join(AQM_DATA, fn), parse_dates=["date"], index_col="date")
            if "volume" in df.columns:
                vols[code] = df["volume"]
    return pd.DataFrame(vols).sort_index()


def main():
    close = load_universe_prices()
    volume = load_universe_volume()
    events = load_disclosure_dates()
    ar = compute_ar(close)
    dollar_vol = close * volume
    trading_days = close.index

    records = []
    for code, disc_dates in events.items():
        if code not in dollar_vol.columns:
            continue
        for d in disc_dates:
            pos = trading_days.searchsorted(d, side="right")
            if pos - LIQ_WINDOW < 0 or pos + CAR_LONG >= len(trading_days):
                continue
            pre_liq = dollar_vol[code].iloc[pos - LIQ_WINDOW: pos].mean()
            if pd.isna(pre_liq):
                continue
            records.append({"code": code, "date": trading_days[pos], "liquidity": pre_liq})

    liq_df = pd.DataFrame(records)
    median_liq = liq_df["liquidity"].median()
    print(f"流動性で層別可能なイベント総数: {len(liq_df)}")
    print(f"中央値（売買代金、円）: {median_liq:,.0f}")

    high = liq_df[liq_df["liquidity"] >= median_liq]
    low = liq_df[liq_df["liquidity"] < median_liq]
    print(f"高流動性群: {len(high)}件 / 低流動性群: {len(low)}件")

    def to_events_dict(df):
        d = {}
        for code, date in zip(df["code"], df["date"]):
            d.setdefault(code, []).append(date)
        return d

    high_events = to_events_dict(high)
    low_events = to_events_dict(low)

    result_high = run_reaction_speed_pipeline(ar, trading_days, high_events, label="RQ-002(高流動性)")
    result_low = run_reaction_speed_pipeline(ar, trading_days, low_events, label="RQ-002(低流動性)")

    for name, r in [("高流動性", result_high), ("低流動性", result_low)]:
        verdict = "支持(p<0.05)" if r["p_value"] < 0.05 else "不支持"
        print(f"[{name}] median={r['median_ratio']:.4f} mean={r['mean_ratio']:.4f} "
              f"p={r['p_value']:.4f} -> {verdict}")


if __name__ == "__main__":
    main()
