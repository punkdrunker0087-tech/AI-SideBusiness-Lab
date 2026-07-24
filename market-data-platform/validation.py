"""検証・正規化レイヤー ―― 保存前にデータ品質を自動確認する。

チェック項目: 欠損値・重複・外れ値・タイムスタンプの順序・異常な価格変化・
データ型の整合性。異常を検知した場合はフラグを立て、原因確認前に下流
（特徴量生成等）で無条件に使われないようにする。
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class ValidationReport:
    symbol: str
    n_rows: int
    issues: dict = field(default_factory=dict)

    @property
    def has_issues(self) -> bool:
        return any(v for v in self.issues.values() if v not in (0, False, None, []))

    def summary(self) -> str:
        lines = [f"検証結果: {self.symbol}（{self.n_rows}行）"]
        for k, v in self.issues.items():
            flag = "⚠️ " if v not in (0, False, None, []) else "○ "
            lines.append(f"  {flag}{k}: {v}")
        return "\n".join(lines)


REQUIRED_DTYPES = {
    "open": "float", "high": "float", "low": "float",
    "close": "float", "adjclose": "float", "volume": "float",
}


def validate(df: pd.DataFrame, symbol: str) -> ValidationReport:
    """OHLCV DataFrame(index=日付)を検証し、レポートを返す。データは変更しない。"""
    issues = {}

    # 欠損値
    issues["欠損値(列別)"] = {c: int(n) for c, n in df.isna().sum().items() if n > 0}

    # 重複インデックス
    issues["重複タイムスタンプ"] = int(df.index.duplicated().sum())

    # タイムスタンプの順序（単調増加か）
    issues["タイムスタンプ逆行"] = not bool(df.index.is_monotonic_increasing)

    # データ型の整合性
    dtype_issues = []
    for col, expect in REQUIRED_DTYPES.items():
        if col not in df.columns:
            dtype_issues.append(f"{col}列が存在しない")
            continue
        if not np.issubdtype(df[col].dtype, np.floating) and not np.issubdtype(df[col].dtype, np.integer):
            dtype_issues.append(f"{col}が数値型でない({df[col].dtype})")
    issues["データ型の不整合"] = dtype_issues

    # OHLC整合性（high >= low, high >= open/close, low <= open/close）
    if {"open", "high", "low", "close"}.issubset(df.columns):
        bad_ohlc = (
            (df["high"] < df["low"]) |
            (df["high"] < df["open"]) | (df["high"] < df["close"]) |
            (df["low"] > df["open"]) | (df["low"] > df["close"])
        )
        issues["OHLC不整合行"] = int(bad_ohlc.sum())

    # 異常な価格変化（分割・データグリッチの疑い）
    if "close" in df.columns:
        ret = df["close"].pct_change()
        issues["±50%超の日次変化"] = int(((ret > 0.5) | (ret < -0.5)).sum())
        # スパイク＆即日反転（1日だけの誤値の典型パターン）
        spike = ((ret < -0.4) & (ret.shift(-1) > 0.6)) | ((ret > 0.6) & (ret.shift(-1) < -0.4))
        issues["スパイク&即日反転(誤値疑い)"] = int(spike.sum())

    # 非正の価格・出来高
    issues["非正の価格"] = int((df[["open", "high", "low", "close"]] <= 0).sum().sum()) \
        if {"open", "high", "low", "close"}.issubset(df.columns) else 0
    issues["負の出来高"] = int((df["volume"] < 0).sum()) if "volume" in df.columns else 0

    return ValidationReport(symbol=symbol, n_rows=len(df), issues=issues)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """軽微な正規化: 重複除去（最後を優先）・時系列ソート・型統一。

    重大な問題（OHLC不整合・巨大な異常値）は自動修復せず、検証レポートで
    フラグを立てるに留める（「原因確認前に下流で無条件に使われないように」）。
    """
    out = df[~df.index.duplicated(keep="last")].sort_index()
    for col in REQUIRED_DTYPES:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out
