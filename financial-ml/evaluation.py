"""モデル評価 ―― 単一指標でなく、時系列外性能・安定性・複雑さ・解釈可能性を見る。"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge

import models as models_mod
import validation


def rank_ic(y_true: pd.Series, y_pred: np.ndarray) -> float:
    """予測順位と実際の順位（ラベル）の相関（Spearman）。"""
    if len(y_true) < 5 or np.std(y_pred) == 0:
        return np.nan
    return float(stats.spearmanr(y_true, y_pred).correlation)


def complexity_score(model) -> str:
    """モデルの複雑さを簡易的に表現する（パラメータ数の目安）。"""
    if isinstance(model, Ridge):
        return f"線形係数 {len(model.coef_)}個"
    if hasattr(model, "n_estimators"):
        return f"決定木{model.n_estimators}本×深さ{model.max_depth}"
    if hasattr(model, "hidden_layer_sizes"):
        return f"隠れ層{model.hidden_layer_sizes}"
    return "不明"


def interpretability_note(name: str, model, feature_cols: list) -> str:
    if hasattr(model, "coef_"):
        top = sorted(zip(feature_cols, model.coef_), key=lambda x: abs(x[1]), reverse=True)
        return "係数で直接解釈可能: " + ", ".join(f"{f}={c:+.3f}" for f, c in top[:3])
    if hasattr(model, "feature_importances_"):
        top = sorted(zip(feature_cols, model.feature_importances_), key=lambda x: x[1], reverse=True)
        return "特徴量重要度で解釈可能: " + ", ".join(f"{f}={i:.3f}" for f, i in top[:3])
    return "解釈は困難（ブラックボックス。SHAP等の事後説明手法が必要）"


def evaluate_across_folds(df: pd.DataFrame, folds: list, seed: int = 0) -> pd.DataFrame:
    """各モデル×各フォールドでOOS性能(rank IC)を計算する。"""
    rows = []
    for fold_i, fold in enumerate(folds):
        train_df = df.loc[df.index.isin(fold.train_idx)]
        test_df = df.loc[df.index.isin(fold.test_idx)]
        X_train, y_train, _ = models_mod.prepare_xy(train_df)
        X_test, y_test, _ = models_mod.prepare_xy(test_df)
        if len(X_train) < 50 or len(X_test) < 20:
            continue

        for name, model in models_mod.build_models(seed).items():
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            ic = rank_ic(y_test, pred)
            rows.append({
                "fold": fold_i, "model": name, "rank_ic": ic,
                "n_train": len(X_train), "n_test": len(X_test),
                "test_range": f"{fold.test_range[0]}〜{fold.test_range[1]}",
                "n_purged": fold.n_purged,
            })
    return pd.DataFrame(rows)


def stability_summary(results: pd.DataFrame) -> pd.DataFrame:
    """モデルごとのOOS性能の平均・安定性（標準偏差）・勝率。"""
    g = results.groupby("model")["rank_ic"]
    return pd.DataFrame({
        "IC平均": g.mean(), "IC標準偏差": g.std(),
        "IC安定性(平均/標準偏差)": g.mean() / g.std(),
        "正のIC割合": results.groupby("model")["rank_ic"].apply(lambda s: (s > 0).mean()),
    }).round(3)
