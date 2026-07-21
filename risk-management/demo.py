"""リスク管理フレームワークの通しデモ（実データ・6銘柄の分散ポート）。

サイジング（逆ボラ/リスクパリティ）→ リスク寄与 → ストップ → ドローダウン →
相関・ストレス → 流動性 → 毎朝チェックリスト、を一気通貫で実演する。
"""
import numpy as np
import pandas as pd

import daily_report
import data_util
import drawdown
import market_risk
import sizing
import stops

# 分散を意図した6銘柄（自動車/電機/銀行/通信/医薬/ゲーム）
PORTFOLIO = ["7203.T", "6758.T", "8306.T", "9433.T", "4502.T", "7974.T"]
BENCH = "1306.T"  # TOPIX ETF


def main():
    print("パネル取得中（6銘柄 + TOPIX）…")
    close, volume = data_util.build_panel(PORTFOLIO, range_="2y")
    bench = data_util.fetch_one(BENCH, "2y")["close"]
    returns = close.pct_change().dropna()
    market_ret = bench.pct_change().reindex(returns.index)
    print(f"  期間 {close.index[0].date()}〜{close.index[-1].date()}  {len(close)}営業日\n")

    cov = sizing.ann_cov(returns)

    # --- 2. ポジションサイジング ---
    w_iv = sizing.inverse_vol(returns)
    w_rp = sizing.risk_parity(cov)
    print("=== ポジションサイジング比較 ===")
    comp = pd.DataFrame({"逆ボラ": w_iv, "リスクパリティ": w_rp}).round(3)
    print(comp.to_string())

    print("\n=== リスク寄与（リスクパリティ配分）===")
    rc = sizing.risk_contribution(w_rp, cov)
    print(rc.assign(pct=(rc["pct"]*100).round(1)).round(4).to_string())
    print(f"  → 寄与率が均等なら分散が効いている。ポートボラ={sizing.portfolio_vol(w_rp,cov)*100:.1f}%")

    # 目標ボラ10%へスケール
    w_target = sizing.vol_target(w_rp, cov, target_vol=0.10)
    lev = float(w_target.sum())
    print(f"  年率ボラ10%目標 → 総エクスポージャー {lev:.2f}"
          f"（{'レバレッジ' if lev>1 else '現金比率あり'}）")

    # --- 3. 損失管理（トヨタで4種ストップの発火例）---
    print("\n=== 損失管理：4種ストップの発火例（7203.T・過去の最悪エントリー付近）===")
    tgt = close["7203.T"].dropna()
    entry = int(np.argmax([tgt.iloc[i] for i in range(len(tgt))]))  # 高値掴みの例
    entry = min(entry, len(tgt) - 30)
    res = stops.evaluate(tgt.reset_index(drop=True), entry, stops.StopConfig())
    print(f"  エントリー日 idx={entry} 価格={tgt.iloc[entry]:.0f} → "
          f"{res['stop_type']} で手仕舞い（{res['holding_days']}日後, "
          f"損益 {res['pnl_pct']*100:+.1f}%）")

    # --- 4. ドローダウン管理 ---
    port_ret = returns @ w_rp
    equity = (1 + port_ret).cumprod()
    print("\n=== ドローダウン管理 ===")
    dd = drawdown.current_state(equity, drawdown.DrawdownPolicy())
    print(f"  最大DD {drawdown.max_drawdown(equity)*100:.1f}%  "
          f"現在DD {dd['drawdown']*100:.1f}% → {dd['action']}")

    # --- 5. 相関監視 ---
    print("\n=== 相関監視：平常時 vs ストレス時 ===")
    print(market_risk.stress_correlation(returns, market_ret).round(3).to_string(index=False))

    # --- 6. ストレステスト ---
    print("\n=== ストレステスト（リスクパリティ配分・対NAV損益）===")
    print(market_risk.stress_test(w_rp, returns).round(4).to_string(index=False))

    # --- 8. 毎朝チェックリスト（全部入り）---
    print("\n")
    print(daily_report.morning_report(w_rp, close, volume, equity, market_ret, nav=1e7))


if __name__ == "__main__":
    main()
