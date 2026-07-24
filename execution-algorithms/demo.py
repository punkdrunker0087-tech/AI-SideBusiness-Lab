"""執行アルゴリズムの通しデモ。

TWAP vs VWAP vs アイスバーグの執行品質比較 → スマート注文ルーティング →
継続的モニタリング、を合成市場で実演する。
"""
import numpy as np

import engine
import iceberg
import impact_model
import market_sim
import monitoring
import smart_router
import tca
import twap
import vwap


N_STEPS = 78          # 5分刻み×6.5時間
TOTAL_QTY = 400_000    # 執行したい親注文の数量（買い）
SIDE = 1


def build_session(seed: int) -> market_sim.MarketSession:
    return market_sim.simulate_session(n_steps=N_STEPS, total_volume=2_000_000,
                                       mid0=3000.0, sigma_daily=0.02, seed=seed)


def run_twap(seed: int):
    session = build_session(seed)
    sched = twap.schedule(TOTAL_QTY, N_STEPS)
    result = engine.simulate_execution(session, sched)
    return tca.analyze(result, session, side=SIDE)


def run_vwap(seed: int, predicted: bool = True):
    session = build_session(seed)
    true_profile = session.volume / session.volume.sum()
    profile = vwap.predicted_profile(true_profile, seed=seed + 500) if predicted else true_profile
    sched = vwap.schedule_from_profile(TOTAL_QTY, profile)
    result = engine.simulate_execution(session, sched)
    return tca.analyze(result, session, side=SIDE)


def run_iceberg(seed: int, display_ratio: float = 0.02):
    session = build_session(seed)
    parent = twap.schedule(TOTAL_QTY, N_STEPS)
    config = iceberg.IcebergConfig(display_size=TOTAL_QTY * display_ratio)
    eff_sched, fill_rates, leak = iceberg.apply_iceberg_schedule(parent, config, TOTAL_QTY)

    params = impact_model.ImpactParams(gamma=impact_model.ImpactParams().gamma * leak)
    result = engine.simulate_execution(session, eff_sched, impact_params=params)
    return tca.analyze(result, session, side=SIDE), fill_rates, leak


def main():
    print("=" * 70)
    print("1. TWAP vs VWAP(予測出来高) vs VWAP(完全な出来高) vs アイスバーグ")
    print("=" * 70)
    seed = 42
    r_twap = run_twap(seed)
    r_vwap_pred = run_vwap(seed, predicted=True)
    r_vwap_perfect = run_vwap(seed, predicted=False)
    r_iceberg, fill_rates, leak = run_iceberg(seed)

    print(tca.format_report("TWAP", r_twap))
    print(tca.format_report("VWAP(予測出来高)", r_vwap_pred))
    print(tca.format_report("VWAP(完全な出来高・理論上限)", r_vwap_perfect))
    print(tca.format_report("アイスバーグ(表示2%)", r_iceberg))
    print(f"  └ アイスバーグ: 平均約定率(刻み別)={fill_rates.mean()*100:.1f}%  "
         f"恒久的インパクト軽減係数={leak:.2f}")

    print("\n" + "=" * 70)
    print("2. VWAPの出来高予測誤差と執行品質の関係")
    print("=" * 70)
    session = build_session(seed)
    true_profile = session.volume / session.volume.sum()
    for noise in [0.0, 0.15, 0.40]:
        pred = vwap.predicted_profile(true_profile, noise_std=noise, seed=seed + 500)
        te = vwap.tracking_error(true_profile, pred)
        sched = vwap.schedule_from_profile(TOTAL_QTY, pred)
        result = engine.simulate_execution(session, sched)
        r = tca.analyze(result, session, side=SIDE)
        print(f"  ノイズ std={noise:.2f}  乖離(tracking error)={te:.3f}  "
             f"IS={r.implementation_shortfall_bps:+.1f}bps  約定率={r.fill_rate*100:.1f}%")

    print("\n" + "=" * 70)
    print("3. スマート注文ルーティング（複数venue・コスト比較）")
    print("=" * 70)
    venues = [
        smart_router.Venue("取引所A(本則)", liquidity_share=0.6, fee_bps=1.0, spread_bps=4.0, latency_ms=5),
        smart_router.Venue("PTS-B", liquidity_share=0.25, fee_bps=0.5, spread_bps=6.0, latency_ms=15),
        smart_router.Venue("PTS-C(高速・高コスト)", liquidity_share=0.15, fee_bps=2.5, spread_bps=3.0, latency_ms=1),
    ]
    step_volume = session.volume[10]
    sigma_step = np.std(np.diff(np.log(session.mid)))
    cmp = smart_router.compare_routing(TOTAL_QTY / N_STEPS, venues, step_volume, sigma_step)
    print(f"  naive配分（流動性比例）: {cmp['naive_allocation']}")
    print(f"    期待コスト = {cmp['naive_cost_bps']:.2f}bps")
    print(f"  smart配分（コスト最小化ウォーターフォール）: {cmp['smart_allocation']}")
    print(f"    期待コスト = {cmp['smart_cost_bps']:.2f}bps")
    print(f"  → smartルーティングによる改善: "
         f"{cmp['naive_cost_bps'] - cmp['smart_cost_bps']:+.2f}bps")

    print("\n" + "=" * 70)
    print("4. 継続的モニタリング（TWAPを20日分シミュレーション）")
    print("=" * 70)
    history = monitoring.run_multi_day(run_twap, n_days=20)
    print(monitoring.summary_report(history))

    print(
        "\n注意: 板情報がないため合成市場（U字型出来高・GBM仲値・平方根法則の"
        "\nマーケットインパクト）での検証。実市場での絶対値は板構造・参加者構成"
        "\nに強く依存するため、ここでは『手法間の相対比較・トレードオフの理解』"
        "\nを目的とする。"
    )


if __name__ == "__main__":
    main()
