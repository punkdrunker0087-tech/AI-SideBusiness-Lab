"""市場データ基盤の通しデモ。

データ取得 → 検証・正規化 → 保存(生/加工済み/メタデータ) →
コーポレートアクション検知 → 特徴量生成・フィーチャーストア登録 →
API経由アクセス(監査ログ) → スケジューリング(更新要否判定)
"""
import datetime

import corporate_actions
import feature_store
import ingestion
import scheduler
import storage
import validation

# 分割イベントを含むことが分かっている銘柄(1306.T: TOPIX ETF、過去に分割あり)
# と、通常の個別株を両方デモに含める。
SYMBOLS = ["1306.T", "7203.T"]


def ingest_and_store(symbol: str):
    print(f"\n--- {symbol} ---")

    # 1. データ取得
    result = ingestion.fetch_daily(symbol, range_="5y")
    print(f"[取得] source={result.source} fetched_at={result.fetched_at} "
          f"行数={len(result.raw)}")
    storage.save_raw(symbol, result.granularity, result.raw)

    # 2. 検証・正規化
    report = validation.validate(result.raw, symbol)
    print(f"[検証] {report.summary()}")
    processed = validation.normalize(result.raw)

    # 4. コーポレートアクション検知（保存前に把握しておく）
    events = corporate_actions.detect_events(processed)
    if not events.empty:
        print(f"[コーポレートアクション] {len(events)}件検出:")
        print(events.head(5).to_string(index=False))
    else:
        print("[コーポレートアクション] 検出なし")

    # 3. 保存（生データ・加工済みデータ・メタデータ）
    storage.save_processed(symbol, result.granularity, processed)
    meta = storage.record_update(
        symbol=symbol, source=result.source, granularity=result.granularity,
        fetched_at=result.fetched_at, n_rows=len(processed),
        validation_issues=report.issues if report.has_issues else {},
        corporate_actions=events["type"].tolist() if not events.empty else [],
    )
    print(f"[保存] 生データ・加工済みデータ・メタデータを記録。"
          f"更新履歴件数={len(meta['history'])}")
    return processed


def main():
    processed_data = {}
    for sym in SYMBOLS:
        processed_data[sym] = ingest_and_store(sym)

    # 5. 特徴量生成 → フィーチャーストア登録
    print("\n" + "=" * 66)
    print("フィーチャーストア: 特徴量の登録と再現性検証")
    print("=" * 66)
    sym = "7203.T"
    df = processed_data[sym]
    price = corporate_actions.apply_adjustment_policy(df, policy="adjclose")
    momentum = price.pct_change(20).rename("momentum_20d")

    reg_entry = feature_store.register_feature(
        name="momentum_20d", symbol=sym, source_df=df,
        feature_series=momentum, method="pct_change(20) on adjclose", version="v1",
    )
    print(f"登録: {reg_entry['name']} / {reg_entry['symbol']} / "
          f"ハッシュ={reg_entry['source_data_hash']} / 計算方法='{reg_entry['method']}'")

    # 同じソースデータで再現性を検証（一致するはず）
    check = feature_store.verify_reproducibility("momentum_20d", sym, df)
    print(f"再現性検証(同一データ): reproducible={check['reproducible']}")

    # ソースデータが変わった場合（1行落とす等）にハッシュが変わることも確認
    tampered = df.iloc[:-5]
    check2 = feature_store.verify_reproducibility("momentum_20d", sym, tampered)
    print(f"再現性検証(データが変わった場合): reproducible={check2['reproducible']}"
          f"（一致しないはず＝改変を検知できている）")

    # 6. API経由アクセス（監査ログ）
    print("\n" + "=" * 66)
    print("API・利用インターフェース: 権限・キャッシュ・監査ログ")
    print("=" * 66)
    import api
    df1 = api.get_processed(sym, caller="research")            # disk read
    df2 = api.get_processed(sym, caller="backtest")             # cache hit
    print(f"research経由: {len(df1)}行 / backtest経由(キャッシュ): {len(df2)}行")
    try:
        api.get_processed(sym, caller="unknown_service")
    except api.PermissionError_ as e:
        print(f"権限チェック: 未許可の呼び出し元を正しく拒否 → {e}")

    print("直近の監査ログ:")
    for entry in api.read_audit_log(5):
        print(f"  {entry['ts']}  {entry['caller']:12s} {entry['action']:28s} {entry['symbol']}")

    # 7. スケジューリング: 更新要否の判定
    print("\n" + "=" * 66)
    print("スケジューリング: データ種別ごとの更新要否判定")
    print("=" * 66)
    meta = storage.load_metadata(sym)
    last_updated = meta["last_updated"]
    for freq in [scheduler.UpdateFrequency.DAILY, scheduler.UpdateFrequency.WEEKLY]:
        check = scheduler.check_staleness(sym, freq, last_updated)
        print(f"  {check.summary()}")

    print(
        "\n注意: 日足のみ実データ対応。ティック/分足は同一設計（粒度別の保存"
        "\nディレクトリ・更新頻度）を拡張すれば対応可能という設計に留める。"
    )


if __name__ == "__main__":
    main()
