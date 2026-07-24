"""7. 運用監視 ―― モデル性能・入力分布・特徴量重要度・ドリフトを継続的に監視する。"""
import numpy as np
import pandas as pd

import models as models_mod


def population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """PSI: 入力データ分布のドリフトを測る。目安: <0.1安定 / 0.1-0.25要注意 / >0.25大きく変化。"""
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if len(expected) < bins or len(actual) < bins:
        return np.nan
    edges = np.percentile(expected, np.linspace(0, 100, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    e_pct = np.clip(np.histogram(expected, edges)[0] / len(expected), 1e-6, None)
    a_pct = np.clip(np.histogram(actual, edges)[0] / len(actual), 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def input_drift_report(df: pd.DataFrame, split: float = 0.5,
                       feature_cols=None) -> pd.DataFrame:
    """特徴量ごとに、前半(学習相当)と後半(運用相当)の分布ドリフト(PSI)を計算する。"""
    feature_cols = feature_cols or models_mod.FEATURE_COLS
    cut = int(len(df) * split)
    rows = []
    for col in feature_cols:
        psi = population_stability_index(df[col].iloc[:cut].values, df[col].iloc[cut:].values)
        rows.append({"feature": col, "psi": psi,
                    "verdict": "○安定" if psi < 0.1 else "△要注意" if psi < 0.25 else "⚠️大きく変化"})
    return pd.DataFrame(rows)


def feature_importance_drift(df: pd.DataFrame, folds: list, seed: int = 0) -> pd.DataFrame:
    """決定木モデルの特徴量重要度が、フォールドを追うごとにどう変化するかを追跡する。"""
    rows = []
    for fold_i, fold in enumerate(folds):
        train_df = df.loc[df.index.isin(fold.train_idx)]
        X_train, y_train, _ = models_mod.prepare_xy(train_df)
        if len(X_train) < 50:
            continue
        model = models_mod.build_models(seed)["決定木系(RandomForest)"]
        model.fit(X_train, y_train)
        for feat, imp in zip(models_mod.FEATURE_COLS, model.feature_importances_):
            rows.append({"fold": fold_i, "feature": feat, "importance": imp})
    return pd.DataFrame(rows)


def performance_trend(results: pd.DataFrame, model_name: str, window: int = 2) -> dict:
    """foldを追った性能(IC)のトレンドを見る。悪化傾向をアラートする。"""
    s = results[results["model"] == model_name].sort_values("fold")["rank_ic"]
    if len(s) < window * 2:
        return {"verdict": "判定不能（フォールド数不足）"}
    recent = s.iloc[-window:].mean()
    earlier = s.iloc[:-window].mean()
    degrading = recent < earlier - 0.02
    return {
        "recent_ic": float(recent), "earlier_ic": float(earlier),
        "verdict": "⚠️ 直近フォールドで性能が悪化傾向" if degrading else "○ 性能は概ね安定",
    }
