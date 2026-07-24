"""フィーチャーストア ―― 特徴量の再現性を確保する。

各特徴量について、元データ・計算方法・更新時刻・バージョンを記録する。
元データのハッシュを取ることで「同じ入力から同じ特徴量が再計算できるか」
を後から検証できる（過去の研究結果の再現に必須）。
"""
import datetime
import hashlib
import json
import os

import pandas as pd

FEATURES_DIR = os.path.join(os.path.dirname(__file__), "data", "features")
REGISTRY_PATH = os.path.join(FEATURES_DIR, "registry.json")


def _hash_dataframe(df: pd.DataFrame) -> str:
    """元データのハッシュ（同一データからの再計算可能性を後で検証するため）。"""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest()[:16]


def _load_registry() -> dict:
    if not os.path.exists(REGISTRY_PATH):
        return {}
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _save_registry(reg: dict):
    os.makedirs(FEATURES_DIR, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)


def register_feature(name: str, symbol: str, source_df: pd.DataFrame,
                     feature_series: pd.Series, method: str, version: str = "v1") -> dict:
    """特徴量を保存し、レジストリに再現性メタデータを記録する。"""
    os.makedirs(os.path.join(FEATURES_DIR, name), exist_ok=True)
    path = os.path.join(FEATURES_DIR, name, f"{symbol}_{version}.csv")
    feature_series.rename(name).to_csv(path)

    reg = _load_registry()
    key = f"{name}/{symbol}/{version}"
    reg[key] = {
        "name": name, "symbol": symbol, "version": version,
        "method": method,
        "source_data_hash": _hash_dataframe(source_df),
        "n_rows": len(feature_series),
        "computed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "path": path,
    }
    _save_registry(reg)
    return reg[key]


def verify_reproducibility(name: str, symbol: str, current_source_df: pd.DataFrame,
                          version: str = "v1") -> dict:
    """登録時のソースデータハッシュと現在のソースデータハッシュを比較する。

    一致すれば「同じ入力データが使われている」ことが保証され、特徴量の
    再計算が過去と同一条件で行えることを意味する。
    """
    reg = _load_registry()
    key = f"{name}/{symbol}/{version}"
    if key not in reg:
        return {"found": False}
    current_hash = _hash_dataframe(current_source_df)
    registered_hash = reg[key]["source_data_hash"]
    return {
        "found": True,
        "registered_hash": registered_hash,
        "current_hash": current_hash,
        "reproducible": current_hash == registered_hash,
        "computed_at": reg[key]["computed_at"],
    }
