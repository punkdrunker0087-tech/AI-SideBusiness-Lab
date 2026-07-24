"""Research Models ―― 推論・信頼度出力・ドリフト監視。

学習済みモデル（本デモではRandomForest）が特徴量から売買シグナルと
信頼度（predict_probaの最大値）を出力する。モデルの当否そのものより、
「推論結果を安全に記録し、ドリフトを監視できる構造」が主眼。
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

import event_log

VERSION = "v1"


def train(features: pd.DataFrame, close: pd.Series, horizon: int = 5, seed: int = 0):
    """翌horizon日で上昇/下落したかを2値分類するモデルを学習する（過去データのみ）。"""
    fwd_ret = close.shift(-horizon) / close - 1
    label = (fwd_ret > 0).astype(int)
    df = pd.concat([features, label.rename("label")], axis=1).dropna()

    model = RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_leaf=20,
                                   random_state=seed)
    model.fit(df[features.columns], df["label"])
    return model


def infer(model, features_row: pd.Series, symbol: str, date, run_id: str = None) -> dict:
    """1時点の特徴量からシグナル・信頼度を出力し、推論イベントを記録する。"""
    if features_row.isna().any():
        result = {"symbol": symbol, "date": str(date.date()), "signal": 0,
                  "confidence": None, "reason": "特徴量に欠損があり推論不可"}
        event_log.log_event("model_inference", result, run_id=run_id)
        return result

    X = features_row.to_frame().T
    proba = model.predict_proba(X)[0]
    pred = int(np.argmax(proba))
    confidence = float(proba[pred])
    signal = 1 if pred == 1 else -1  # +1: 上昇予測(買い方向) / -1: 下落予測(売り方向)

    result = {
        "symbol": symbol, "date": str(date.date()), "signal": signal,
        "confidence": confidence, "model_version": VERSION,
    }
    event_log.log_event("model_inference", result, run_id=run_id)
    return result


def population_stability_index(expected: np.ndarray, actual: np.ndarray,
                              bins: int = 10, min_per_bin: int = 10) -> float:
    """PSI: 推論結果(信頼度等)の分布ドリフトを測る。

    実装時に2つのバグを実際に踏んで修正した:
      1. 決定木系モデルの確信度が離散値に集中し、分位点ビン境界が重複すると
         `np.histogram`がゼロ幅ビンを作りPSIを異常に膨張させる
         → `np.unique`で境界の重複を除去
      2. サンプル数に対してビン数が多すぎると、1ビンあたりの期待件数が
         数件しかなく、偶然の空ビンでPSIが人為的に大きくなる
         （例: 40件を10ビンに割ると1ビン平均4件→空ビンが出やすい）
         → サンプル数に応じてビン数を自動的に減らす（1ビンあたり最低
         min_per_bin件を確保できる数に制限）
    """
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if len(expected) < bins or len(actual) < bins:
        return np.nan

    effective_bins = max(2, min(bins, min(len(expected), len(actual)) // min_per_bin))
    if effective_bins < 2:
        return np.nan

    raw_edges = np.percentile(expected, np.linspace(0, 100, effective_bins + 1))
    edges = np.unique(raw_edges)
    if len(edges) < 3:
        return np.nan
    edges[0], edges[-1] = -np.inf, np.inf
    e_pct = np.clip(np.histogram(expected, edges)[0] / len(expected), 1e-6, None)
    a_pct = np.clip(np.histogram(actual, edges)[0] / len(actual), 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))
