"""研究・検証向けシステムアーキテクチャの通しデモ。

Data Providers → Validation → Feature Pipeline → Research Models
→ Paper Trading Layer → Monitoring Dashboard を実データで一気通貫実行し、
イベントログ・アラート・リコンシリエーションの動作を確認する。

⚠️ 自動発注・ブローカー接続は一切行わない（仮想売買のみ）。
"""
import event_log
import monitoring
import orchestrator


def main():
    event_log.clear_log()  # デモの再実行のためログをリセット（実運用では消さない）

    symbols = ["7203.T", "6758.T", "9432.T"]
    print(f"パイプライン実行中（銘柄: {symbols}）…\n")
    result = orchestrator.run_pipeline(symbols, range_="2y", sim_days=120)

    print("=" * 66)
    print(f"実行完了 run_id={result['run_id']}  "
         f"シミュレーション日数={result['n_days_simulated']}  "
         f"平均推論レイテンシ={result['avg_inference_latency_ms']:.2f}ms")
    print("=" * 66)

    print("\n" + monitoring.dashboard(result["account"], run_id=result["run_id"]))

    print("\n=== リコンシリエーション結果 ===")
    recon = result["reconciliation"]
    print(f"ポジション照合: {recon['positions']['verdict']} "
         f"({recon['positions']['n_symbols_checked']}銘柄チェック)")
    print(f"モデル判断照合: {recon['decisions']['verdict']} "
         f"({recon['decisions']['n_fills_checked']}約定チェック)")

    print("\n=== イベントログのサマリ（種別ごとの件数） ===")
    all_events = event_log.read_events(run_id=result["run_id"])
    from collections import Counter
    counts = Counter(e["event_type"] for e in all_events)
    for etype, n in counts.items():
        print(f"  {etype:20s} {n}件")

    print("\n=== 直近の仮想約定（最大5件） ===")
    fills = event_log.read_events("paper_fill", run_id=result["run_id"], n=5)
    for f in fills:
        p = f["payload"]
        print(f"  {p['date']} {p['symbol']:8s} trade_qty={p['trade_qty']:+.0f} "
             f"price={p['price']:.1f} cost={p['cost']:.1f}")

    print("\n=== 監査例: ある日の判断根拠を追跡する ===")
    if fills:
        target = fills[-1]["payload"]
        print(f"対象: {target['symbol']} {target['date']}")
        matching_inference = [
            e for e in event_log.read_events("model_inference", run_id=result["run_id"])
            if e["payload"]["symbol"] == target["symbol"] and e["payload"]["date"] == target["date"]
        ]
        if matching_inference:
            inf = matching_inference[0]["payload"]
            print(f"  モデル推論: signal={inf['signal']:+d} confidence={inf['confidence']:.3f}")
        print(f"  → 仮想約定: trade_qty={target['trade_qty']:+.0f} "
             f"(信頼度が閾値0.55以上だったか等が判断根拠として再構成できる)")

    print(
        "\n注意: これは研究・検証用のペーパートレード基盤。自動発注・ブローカー"
        "\n接続は含まない。実際の通知(SMS/メール)は行わずログ記録+標準出力に留める。"
    )


if __name__ == "__main__":
    main()
