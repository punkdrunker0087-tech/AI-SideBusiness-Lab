"""金融ML研究フレームワークの通しデモ（実データ・25銘柄・5年）。

1.仮説 → 2.データ整備(先読み検証込み) → 3.特徴量設計 → 4.モデル比較
→ 5.Purged/Embargo検証(vs 単純分割との比較) → 6.ロバスト性(レジーム別)
→ 7.運用監視
"""
import numpy as np
import pandas as pd

import data_prep
import data_util
import evaluation
import features
import hypothesis
import models as models_mod
import monitoring
import robustness
import validation


def main():
    print(f"研究仮説: {hypothesis.HYPOTHESIS.question}")
    print(f"根拠: {hypothesis.HYPOTHESIS.rationale[:60]}…\n")

    print("パネル取得中（25銘柄・5年）…")
    close, volume = data_util.build_panel(range_="5y")
    bench = data_util.fetch_one("1306.T", "5y")["close"]
    print(f"  期間 {close.index[0].date()}〜{close.index[-1].date()}  {close.shape[1]}銘柄\n")

    # --- 2. データ整備 ---
    print("=" * 66)
    print("Stage 2: データ整備（時系列整合性・将来情報混入の自動検証）")
    print("=" * 66)
    integrity = data_prep.check_time_series_integrity(close)
    print(f"  重複日付={integrity['重複日付']}  日付逆行={integrity['日付逆行']}  "
         f"欠損あり銘柄数={len(integrity['欠損値(銘柄別)'])}  "
         f"異常値あり銘柄数={len(integrity['±50%超の異常値(銘柄別)'])}")
    close_clean = data_prep.handle_missing_and_outliers(close)

    check_dates = list(close_clean.index[::80])[2:8]  # 適当な間隔でサンプリング
    leak_check = data_prep.assert_no_future_leakage(
        lambda c: features.cross_sectional_zscore(features.momentum(c, 120)),
        close_clean, check_dates,
    )
    print(f"  先読み検証(momentum_120): {leak_check['verdict']} "
         f"({leak_check['n_checked']}日中{leak_check['n_mismatches']}件不一致)")

    # --- 3. 特徴量設計 ---
    print("\n" + "=" * 66)
    print("Stage 3: 特徴量設計")
    print("=" * 66)
    dataset = features.build_dataset(close_clean, volume, horizon=hypothesis.HYPOTHESIS.horizon_days)
    print(f"  データセット行数(date×symbol)={len(dataset)}  "
         f"特徴量={models_mod.FEATURE_COLS}")

    # --- 5. 時系列検証（Purged/Embargo vs 単純分割の比較） ---
    print("\n" + "=" * 66)
    print("Stage 5: 時系列検証 ―― Purge/Embargoの効果")
    print("=" * 66)
    horizon = hypothesis.HYPOTHESIS.horizon_days
    folds_purged = validation.purged_walk_forward(dataset, "date", horizon, n_splits=4, embargo_days=5)
    folds_naive = validation.naive_walk_forward(dataset, "date", n_splits=4)
    for f in folds_purged:
        print(f"  [Purged] test={f.test_range}  train末尾までPurge除去={f.n_purged}件")

    results_purged = evaluation.evaluate_across_folds(dataset, folds_purged)
    results_naive = evaluation.evaluate_across_folds(dataset, folds_naive)
    print("\n  Purged/Embargoあり:")
    print(evaluation.stability_summary(results_purged).to_string())
    print("\n  Purge/Embargoなし（単純分割・楽観的になりやすい比較対象）:")
    print(evaluation.stability_summary(results_naive).to_string())

    # --- 4. モデル比較の複雑さ・解釈可能性 ---
    print("\n" + "=" * 66)
    print("Stage 4: モデルの複雑さ・解釈可能性（最終フォールドで学習した場合）")
    print("=" * 66)
    last_fold = folds_purged[-1]
    train_df = dataset.loc[dataset.index.isin(last_fold.train_idx)]
    X_train, y_train, _ = models_mod.prepare_xy(train_df)
    for name, model in models_mod.build_models().items():
        model.fit(X_train, y_train)
        print(f"  [{name}] 複雑さ: {evaluation.complexity_score(model)}")
        print(f"    解釈可能性: {evaluation.interpretability_note(name, model, models_mod.FEATURE_COLS)}")

    # --- 6. ロバスト性評価（レジーム別） ---
    print("\n" + "=" * 66)
    print("Stage 6: ロバスト性評価 ―― 強気/弱気レジーム別のOOS性能")
    print("=" * 66)
    regimes = robustness.classify_regime(bench)
    regime_results = robustness.evaluate_by_regime(dataset, folds_purged, regimes)
    if not regime_results.empty:
        print(robustness.regime_stability_report(regime_results).to_string())
    else:
        print("  レジーム別サンプルが不足のためスキップ")

    # --- 7. 運用監視 ---
    print("\n" + "=" * 66)
    print("Stage 7: 運用監視 ―― 入力分布ドリフト・特徴量重要度・性能トレンド")
    print("=" * 66)
    drift = monitoring.input_drift_report(dataset)
    print(drift.to_string(index=False))

    imp_drift = monitoring.feature_importance_drift(dataset, folds_purged)
    if not imp_drift.empty:
        pivot = imp_drift.pivot(index="feature", columns="fold", values="importance")
        print("\n  決定木モデルの特徴量重要度（フォールド別）:")
        print(pivot.round(3).to_string())

    for model_name in results_purged["model"].unique():
        trend = monitoring.performance_trend(results_purged, model_name)
        print(f"\n  [{model_name}] 性能トレンド: {trend.get('verdict')}")

    print(
        "\n注意: 25銘柄・5年という小規模な検証。IC水準は小さく、"
        "\n『複雑なモデルほど良い』という結果にはなっていない点に注目。"
        "\nPurge/Embargoの有無で性能推定がどう変わるかを必ず比較すること。"
    )


if __name__ == "__main__":
    main()
