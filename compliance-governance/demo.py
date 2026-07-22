"""コンプライアンス&ガバナンス・フレームワークの通しデモ。

1.ガバナンス構造 → 2.規制インベントリ → 3.取引前リスクコントロール
→ 4.ポジション限度 → 5.市場公正性 → 6.最良執行 → 8.変更管理
→ 9.インシデント対応 → 10.レビュー計画 → 11.税務記録 → 12.KPI
"""
import datetime

import audit_log
import best_execution as be
import change_management as cm
import governance as gov
import incident_response as ir
import kpi_dashboard
import market_integrity as mi
import position_limits as pl
import pretrade_controls as pc
import regulatory_inventory as ri
import review_calendar as rc
import tax_records as tr


def main():
    audit_log.clear()

    print("=" * 66)
    print("1. ガバナンス構造（三線防衛モデル・職務分掌）")
    print("=" * 66)
    dev = gov.Person("開発者A", gov.Line.FIRST)
    risk_mgr = gov.Person("リスク管理者B", gov.Line.SECOND, can_approve=True)
    try:
        gov.require_approval(dev, dev, "戦略パラメータ変更")
    except gov.SegregationOfDutiesError as e:
        print(f"  ⚠️ 職務分掌違反を検知（自己承認の試行）: {e}")
    approval = gov.require_approval(dev, risk_mgr, "戦略パラメータ変更", audit_log.record)
    print(f"  ○ 正規の承認: {approval['proposer']}({approval['proposer_line']}) → "
         f"{approval['approver']}({approval['approver_line']})")

    print("\n" + "=" * 66)
    print("2. 規制インベントリ")
    print("=" * 66)
    inventory = ri.build_inventory()
    print(f"  {len(inventory)}件の規制を管理台帳に登録")
    for e in ri.EXAMPLE_TEMPLATE[:3]:
        print(f"    - {e.name}: 責任者={e.owner}")

    print("\n" + "=" * 66)
    print("3. 取引前リスクコントロール")
    print("=" * 66)
    limits = pc.PreTradeLimits(max_order_quantity=5000, max_notional=30_000_000)
    health = pc.SystemHealth()
    orders_to_check = [
        pc.OrderRequest("7203.T", 100, 2950, 2950, 0),      # 正常
        pc.OrderRequest("7203.T", 100, 29500, 2950, 0),      # 誤入力（価格乖離）
        pc.OrderRequest("7203.T", 20000, 2950, 2950, 0),     # 数量超過
    ]
    for o in orders_to_check:
        r = pc.run_all_checks(o, limits, health)
        print(f"  数量{o.quantity} 指値{o.limit_price} → {r['decision']} "
             f"(NG項目: {r['failed_checks'] or 'なし'})")

    print("\n" + "=" * 66)
    print("4. ポジション限度（ソフト/ハード）")
    print("=" * 66)
    levels = {
        "個別銘柄": pl.LimitLevel("個別銘柄", soft_limit=3_000_000, hard_limit=5_000_000),
        "セクター": pl.LimitLevel("セクター", soft_limit=8_000_000, hard_limit=12_000_000),
    }
    exposures = {
        "個別銘柄": {"7203.T": 3_500_000, "6758.T": 1_000_000},
        "セクター": {"自動車": 4_500_000, "電機": 9_000_000},
    }
    breaches = pl.check_all_levels(exposures, levels)
    print(pl.format_breaches(breaches))

    print("\n" + "=" * 66)
    print("5. 市場公正性モニタリング")
    print("=" * 66)
    synthetic_fills = [
        {"order_id": "1", "account": "X", "symbol": "7203.T", "side": "buy",
        "quantity": 100, "price": 2950, "status": "fill", "ts": "2026-07-22T10:00:00"},
        {"order_id": "2", "account": "X", "symbol": "7203.T", "side": "sell",
        "quantity": 100, "price": 2950, "status": "fill", "ts": "2026-07-22T10:00:00"},
    ]
    synthetic_orders = [
        {"order_id": str(i), "account": "Y", "symbol": "6758.T", "side": "buy",
        "quantity": 10, "price": 3300, "status": "cancel" if i % 10 != 0 else "fill",
        "ts": f"2026-07-22T10:{i:02d}:00"} for i in range(30)
    ]
    surveillance = mi.run_surveillance(synthetic_orders, synthetic_fills)
    print(f"  検知件数: {surveillance['n_flags']}  人によるレビュー要否: "
         f"{surveillance['requires_human_review']}")
    for f in surveillance["flags"]:
        print(f"    [{f['type']}] {f['detail']}")

    print("\n" + "=" * 66)
    print("6. 最良執行の記録")
    print("=" * 66)
    exec_records = [
        be.ExecutionRecord("2026-07-22T10:00:00", "7203.T", "取引所A", 2951.5, 2950.0, 1.0),
        be.ExecutionRecord("2026-07-22T10:05:00", "7203.T", "PTS-B", 2952.0, 2950.0, 0.5),
    ]
    for r in exec_records:
        be.record_execution(r)
    print(be.quality_summary(exec_records).to_string())

    print("\n" + "=" * 66)
    print("8. アルゴリズム変更管理（状態機械）")
    print("=" * 66)
    try:
        bad_cr = cm.ChangeRequest("CR-BAD", "テスト", "テスト範囲")
        bad_cr.advance(cm.ChangeState.APPROVED, "テストを飛ばして承認しようとする", "誰か")
    except cm.InvalidTransitionError as e:
        print(f"  ⚠️ 不正遷移を検知（テスト工程の省略）: {e}")

    cr = cm.full_workflow_example(
        "CR-001", "シグナル閾値の調整", "aqm-strategy/strategy.py",
        "バックテストで想定通りの挙動を確認", "リスク評価: 低",
        dev, risk_mgr,
    )
    print(f"  ○ 正規のフロー完了: {cr.change_id} 最終状態={cr.state.value}")
    for h in cr.history:
        print(f"    {h['from']} → {h['to']} ({h['actor']})")

    print("\n" + "=" * 66)
    print("9. インシデント対応")
    print("=" * 66)
    incident = ir.Incident("INC-001", "取引前チェックの応答遅延を検知", ir.Severity.HIGH)
    incident.initial_response("監視チームが確認・該当戦略を一時停止", "オンコール担当")
    incident.escalate("オンコール担当")
    incident.root_cause("データフィードの遅延が原因と特定", "開発者A")
    incident.recover("フィード復旧・戦略再開", "オンコール担当")
    incident.post_mortem("フィード遅延の監視アラートを追加", "リスク管理者B")
    print(f"  最終状態: {incident.stage.value}  "
         f"検知→初動: {incident.time_to_initial_response_seconds():.1f}秒")

    print("\n" + "=" * 66)
    print("10. レビュー計画")
    print("=" * 66)
    rc.complete_review("daily", "例外なし", "オンコール担当")
    today = datetime.date.today()
    last_completed = {
        "daily": today.isoformat(),
        "weekly": (today - datetime.timedelta(days=10)).isoformat(),
        "monthly": (today - datetime.timedelta(days=20)).isoformat(),
    }
    for row in rc.next_due_report(last_completed):
        print(f"  {row}")

    print("\n" + "=" * 66)
    print("11. 税務記録")
    print("=" * 66)
    lots = [tr.TaxLot("7203.T", "2025-01-15", "2026-07-20", 2500, 2950, 100, fees=500)]
    for lot in lots:
        tr.record_lot(lot)
    print(tr.summarize(lots).to_string(index=False))
    print("  ⚠️ 税務助言ではない。実際の申告前には税理士等の専門家に確認すること。")

    print("\n" + "=" * 66)
    print("12. KPIダッシュボード")
    print("=" * 66)
    kpis = kpi_dashboard.compute_kpis()
    print(kpi_dashboard.format_dashboard(kpis))

    print(
        "\n注意: 本フレームワークは統制・追跡・承認ワークフローの実装であり、"
        "\n自動発注・ブローカー接続は一切含まない。規制インベントリの内容は"
        "\n例示であり法的助言ではない。"
    )


if __name__ == "__main__":
    main()
