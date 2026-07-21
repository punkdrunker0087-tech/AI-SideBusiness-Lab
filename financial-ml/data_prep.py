"""2. データ整備 ―― 時系列整合性・欠損/外れ値処理・将来情報の混入防止。

コーポレートアクション対応はadjclose使用で吸収済み（`data_util.py`）。
ここでは残りの整合性チェックと、**将来情報が混入していないことの
自動検証**を行う。
"""
import numpy as np
import pandas as pd


def check_time_series_integrity(close: pd.DataFrame) -> dict:
    """タイムスタンプの整合性・欠損・外れ値を確認する。"""
    issues = {
        "重複日付": int(close.index.duplicated().sum()),
        "日付逆行": not bool(close.index.is_monotonic_increasing),
        "欠損値(銘柄別)": {c: int(n) for c, n in close.isna().sum().items() if n > 0},
    }
    ret = close.pct_change()
    outliers = ((ret.abs() > 0.5)).sum()
    issues["±50%超の異常値(銘柄別)"] = {c: int(n) for c, n in outliers.items() if n > 0}
    return issues


def handle_missing_and_outliers(close: pd.DataFrame, outlier_threshold: float = 0.5) -> pd.DataFrame:
    """欠損は前方補完、異常値（±50%超の日次変化）はNaN化して補間する。

    過去のみを参照するffillと、前後からの補間(interpolate)を使う。
    """
    ret = close.pct_change()
    is_outlier = ret.abs() > outlier_threshold
    cleaned = close.mask(is_outlier)
    cleaned = cleaned.interpolate(limit_direction="both").ffill()
    return cleaned


def assert_no_future_leakage(feature_fn, close: pd.DataFrame, check_dates: list,
                             atol: float = 1e-9) -> dict:
    """将来情報の混入防止を自動検証する。

    考え方: ある日付tの特徴量値が「未来を知らなくても計算できる」なら、
    そのt以降のデータを切り落として計算しても同じ値になるはずである。
    切り落として計算した値と、全期間データで計算した値を比較し、
    一致すれば「その特徴量関数は先読みしていない」ことの強い証拠になる。

    feature_fn: pd.DataFrame(close) -> pd.DataFrame(同shapeの特徴量) を返す関数
    """
    full_features = feature_fn(close)
    mismatches = []
    for d in check_dates:
        truncated = close.loc[:d]
        if len(truncated) < 10:
            continue
        truncated_features = feature_fn(truncated)
        if d not in truncated_features.index or d not in full_features.index:
            continue
        a = truncated_features.loc[d]
        b = full_features.loc[d]
        diff = (a - b).abs()
        if (diff > atol).any():
            bad_cols = diff[diff > atol].index.tolist()
            mismatches.append({"date": str(d.date()), "mismatched_columns": bad_cols})

    return {
        "n_checked": len(check_dates),
        "n_mismatches": len(mismatches),
        "mismatches": mismatches,
        "verdict": "○ 先読みなし（切り詰めても値が一致）" if not mismatches
                  else "⚠️ 先読みの疑い（切り詰めると値が変わる特徴量がある）",
    }
