"""6. ロバスト性評価 ―― 異なる期間・市場環境で再現するかを確認する。"""
import numpy as np
import pandas as pd

import evaluation
import models as models_mod


def classify_regime(bench_close: pd.Series, window: int = 60) -> pd.Series:
    """ベンチマークのトレンドから強気/弱気を判定する（先読みなし）。"""
    ma = bench_close.rolling(window).mean()
    return pd.Series(np.where(bench_close > ma, "強気", "弱気"), index=bench_close.index)


def evaluate_by_regime(df: pd.DataFrame, folds: list, regimes: pd.Series, seed: int = 0) -> pd.DataFrame:
    """各フォールドのテスト期間を、日付ごとのレジームで分割してIC評価する。"""
    rows = []
    for fold_i, fold in enumerate(folds):
        train_df = df.loc[df.index.isin(fold.train_idx)]
        test_df = df.loc[df.index.isin(fold.test_idx)].copy()
        test_df["regime"] = pd.to_datetime(test_df["date"]).map(regimes)

        X_train, y_train, _ = models_mod.prepare_xy(train_df)
        if len(X_train) < 50:
            continue

        for name, model in models_mod.build_models(seed).items():
            model.fit(X_train, y_train)
            for regime_label, sub in test_df.groupby("regime"):
                X_test, y_test, _ = models_mod.prepare_xy(sub)
                if len(X_test) < 20:
                    continue
                pred = model.predict(X_test)
                ic = evaluation.rank_ic(y_test, pred)
                rows.append({"fold": fold_i, "model": name, "regime": regime_label,
                            "rank_ic": ic, "n": len(X_test)})
    return pd.DataFrame(rows)


def regime_stability_report(regime_results: pd.DataFrame) -> pd.DataFrame:
    """モデル×レジームでのIC平均。レジームによって符号が反転するかを見る。"""
    return regime_results.groupby(["model", "regime"])["rank_ic"].mean().unstack().round(3)
