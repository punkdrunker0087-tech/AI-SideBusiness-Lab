"""定量シグナル研究フレームワークの通しデモ（実データ・25銘柄クロスセクション）。

1.仮説 → 3.特徴量 → 4.IC評価 → 6.レジーム別 → 7.統合(冗長性) → 8.監視(PSI)
を一気通貫で実演する（2.データ分類・5.ロバスト性はREADMEで解説）。
"""
import numpy as np
import pandas as pd

import data_util
import evaluation
import features as ft
import hypothesis
import integration
import monitoring
import regime


def main():
    print("パネル取得中（25銘柄・5年）…")
    close, volume = data_util.build_panel(range_="5y")
    bench = data_util.fetch_one("1306.T", "5y")["close"]
    print(f"  期間 {close.index[0].date()}〜{close.index[-1].date()}  "
          f"{close.shape[1]}銘柄 {close.shape[0]}営業日\n")

    feats = ft.build_all(close, volume)
    feats_z = {n: ft.cross_sectional_zscore(ft.winsorize_cross(f)) for n, f in feats.items()}

    # --- 1+4: 仮説ごとにIC評価し、仮説の符号と整合するか判定 ---
    print("=" * 66)
    print("Stage 1+4: 仮説立案 → IC評価（横断・順位IC・20日先リターン）")
    print("=" * 66)
    fwd20 = ft.forward_return(close, 20)
    for h in hypothesis.REGISTRY:
        fz = feats_z[h.feature]
        s = evaluation.ic_summary(evaluation.ic_series(fz, ft.forward_return(close, h.horizon_days)))
        icm = s.get("ic_mean", np.nan)
        print(f"\n  【{h.name}】{h.rationale[:34]}…")
        print(f"    IC平均={icm:+.3f}  IC_IR={s.get('ic_ir', np.nan):+.2f}  "
              f"勝率={s.get('hit_rate', np.nan)*100:.0f}%  t値={s.get('t_stat', np.nan):+.1f}"
              f"  期待符号={'+' if h.expected_sign>0 else '−'}")
        print(f"    → {h.verdict(icm)}")  # verdict内でexpected_signを考慮

    # --- 4b: IC減衰（モメンタムの効果はどの時間軸か）---
    print("\n" + "=" * 66)
    print("Stage 4b: IC減衰（momentum_120）")
    print("=" * 66)
    print(evaluation.ic_decay(feats_z["momentum_120"], close).round(3).to_string(index=False))

    # --- 6: レジーム別IC ---
    print("\n" + "=" * 66)
    print("Stage 6: レジーム別IC（momentum_120・トレンド局面で分ける）")
    print("=" * 66)
    regs = regime.classify_regimes(bench)
    print(regime.ic_by_regime(feats_z["momentum_120"], fwd20, regs, "trend").round(3).to_string(index=False))
    print(regime.ic_by_regime(feats_z["momentum_120"], fwd20, regs, "vol").round(3).to_string(index=False))

    # --- 7: シグナル統合（冗長性チェック）---
    print("\n" + "=" * 66)
    print("Stage 7: シグナル統合 ―― 特徴量間の相関（冗長性）")
    print("=" * 66)
    print(integration.signal_correlation(feats_z).round(2).to_string())
    combo = integration.ic_weighted_combine(feats_z, fwd20)
    s_combo = evaluation.ic_summary(evaluation.ic_series(combo, fwd20))
    print(f"\n  IC加重合成シグナルのIC平均={s_combo.get('ic_mean', np.nan):+.3f} "
          f"IR={s_combo.get('ic_ir', np.nan):+.2f}（単一より安定するか）")

    # --- 8: 監視（分布ドリフト PSI）---
    print("\n" + "=" * 66)
    print("Stage 8: 運用後監視 ―― 特徴量分布のドリフト（前半 vs 後半）")
    print("=" * 66)
    for n, f in feats.items():
        d = monitoring.drift_report(f)
        print(f"  {n:16s} PSI={d['psi']:.3f}  {d['verdict']}")

    print("\n注意: これは研究デモ。ICが有意でも取引コスト・容量・レジーム変化で"
          "\n実運用の成績は変わる。仮説→検証→再現性の順序を守ることが本質。")


if __name__ == "__main__":
    main()
