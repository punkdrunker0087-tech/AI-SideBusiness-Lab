"""マーケットメイキングの通しデモ。

1. リスク回避度(γ)を変えたときの「在庫リスク vs スプレッド収益」トレードオフ
   （Avellaneda-Stoikovシミュレーション）
2. 在庫制限とヘッジの動作確認
3. PnL分解（スプレッド収益 vs 逆選択コスト）
4. 実データでのマイクロストラクチャー代理指標（Rollスプレッド・Amihud非流動性）
"""
import numpy as np
import pandas as pd
import requests

import inventory as inv_mod
import metrics
import microstructure as micro
import quoting
import simulation

CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch(symbol: str, range_: str = "2y", retries: int = 3) -> pd.DataFrame:
    last_err = None
    for _ in range(retries):
        try:
            r = requests.get(f"{CHART}/{symbol}",
                             params={"range": range_, "interval": "1d",
                                     "includeAdjustedClose": "true"},
                             headers=_HEADERS, timeout=25).json()
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
    else:
        raise RuntimeError(f"{symbol} の取得に失敗: {last_err}")
    res = r["chart"]["result"][0]
    ind = res["indicators"]
    close = ind["adjclose"][0]["adjclose"] if ind.get("adjclose") else ind["quote"][0]["close"]
    return pd.DataFrame(
        {"date": pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_localize(None),
         "close": close, "volume": ind["quote"][0]["volume"]}
    ).dropna(subset=["close"]).set_index("date").sort_index()


def main():
    m = simulation.MarketParams(sigma=2.0, A=140, kappa=1.5, n_steps=8000, dt=0.005)

    print("=" * 70)
    print("1. リスク回避度(γ)によるトレードオフ ―― 在庫リスク vs スプレッド収益")
    print("=" * 70)
    rows = []
    for gamma in [0.01, 0.05, 0.1, 0.3, 0.6]:
        q = quoting.QuoteParams(gamma=gamma, kappa=1.5, sigma=2.0)
        res = simulation.run(q, m, seed=7)
        inv = metrics.inventory_stats(res)
        rar = metrics.risk_adjusted_return(res)
        fr = metrics.fill_rate(res)
        rows.append({
            "gamma": gamma, "約定数": fr["total_fills"],
            "在庫std": inv["inventory_std"], "在庫最大絶対値": inv["inventory_max_abs"],
            "Sharpe/step": rar["sharpe_per_step"], "累積PnL": rar["total_pnl"],
        })
    df = pd.DataFrame(rows)
    print(df.round(3).to_string(index=False))
    print("\n  → γを上げるほど在庫std・最大在庫は下がるが、約定数・PnLも減る。")
    print("    『在庫を絞る（安全運転）』と『スプレッドを稼ぐ（積極運転）』は表裏一体。")

    print("\n" + "=" * 70)
    print("2. 在庫制限とヘッジ ―― ハードリミットに達したら片側クォート停止")
    print("=" * 70)
    limits = inv_mod.InventoryLimits(soft_limit=3.0, hard_limit=5.0)
    q_aggressive = quoting.QuoteParams(gamma=0.01, kappa=1.5, sigma=2.0)  # 在庫が張りやすい設定
    res_limited = simulation.run(q_aggressive, m, limits=limits, seed=7)
    inv = metrics.inventory_stats(res_limited)
    print(f"  制限なし相当(γ=0.01)の在庫最大絶対値: 6.0 (上記表より)")
    print(f"  在庫制限あり(soft=3, hard=5)の在庫最大絶対値: {inv['inventory_max_abs']:.1f}"
          f"  → {'制限が効いている' if inv['inventory_max_abs'] <= 5.0 else '制限超過(要確認)'}")
    hedge = inv_mod.hedge_size(res_limited.inventory_path[-1], target=0.0, hedge_ratio=0.5)
    print(f"  最終在庫 {res_limited.inventory_path[-1]:.0f} → 50%部分ヘッジで "
          f"{hedge:+.1f} 単位の外部ヘッジが必要")

    print("\n" + "=" * 70)
    print("3. PnL分解（γ=0.1・標準設定） ―― スプレッド収益 vs 逆選択コスト")
    print("=" * 70)
    q_std = quoting.QuoteParams(gamma=0.1, kappa=1.5, sigma=2.0)
    res_std = simulation.run(q_std, m, seed=7)
    dec = metrics.pnl_decomposition(res_std)
    print(f"  1約定あたり スプレッド収益={dec['spread_pnl_per_fill']:.3f}  "
          f"逆選択コスト={dec['adverse_selection_pnl_per_fill']:.3f}")
    print("  → この合成市場には情報優位トレーダーがいないため、逆選択はほぼゼロが正しい。")
    print("    実市場では情報優位者の存在で逆選択コストが正に効き、スプレッド収益を削る。")

    print("\n" + "=" * 70)
    print("4. マイクロストラクチャー代理指標（実データ・日次OHLCVの限界内）")
    print("=" * 70)
    print("  ⚠️ 板情報がないため『板の厚さ』『キャンセル率』『注文フロー』は")
    print("     シミュレーションでのみ厳密評価可能。ここでは日次データからの代理指標のみ。")
    for sym, name in [("7203.T", "トヨタ(大型・高流動性)"), ("9020.T", "JR東日本")]:
        df = fetch(sym)
        s = micro.summary(df["close"], df["volume"])
        print(f"\n  {sym} {name}:")
        print(f"    Roll実効スプレッド推定: {s['roll_spread_mean']:.2f}円 "
              f"(推定可能な日の割合 {s['roll_spread_estimable_pct']*100:.0f}%)")
        print(f"    Amihud非流動性        : {s['amihud_illiquidity_mean']:.2e}"
              f"  （大型株のため極小＝流動性が高いことの裏付け）")
        print(f"    実現ボラ(年率)        : {s['realized_vol_mean']*100:.1f}%")

    print(
        "\n注意: 本デモはAvellaneda-Stoikov型の合成市場での設計検証。実際の収益性は"
        "\n実市場の板・手数料・レイテンシ・情報優位トレーダーの存在に強く依存し、"
        "\nここでは扱わない。マーケットメイキングは執行速度で機関投資家に劣後する"
        "\nリテールには構造的に不利な領域である点に留意（LEARNING.md参照）。"
    )


if __name__ == "__main__":
    main()
