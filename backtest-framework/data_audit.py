"""Stage 1: データ監査 ―― 検証の前に、データそのものを疑う。

「バックテストは勝っていたのに実運用で負ける」の何割かは、戦略以前に
データの欠陥（欠損・重複・異常値・未調整の分割・タイムスタンプの乱れ）が原因。
このモジュールはOHLCV系列を受け取り、問題点をレポートする。
"""
import numpy as np
import pandas as pd


def audit(df: pd.DataFrame, price_col: str = "close") -> dict:
    """OHLCV DataFrame（index=日付）を監査し、所見の辞書を返す。"""
    report = {}
    n = len(df)
    report["n_rows"] = n
    if n == 0:
        return report

    # 1) 欠損値
    report["missing_by_col"] = df.isna().sum().to_dict()

    # 2) 重複インデックス（同一日付が複数）
    report["duplicate_index"] = int(df.index.duplicated().sum())

    # 3) タイムスタンプの単調性・重複・逆行
    report["index_monotonic_increasing"] = bool(df.index.is_monotonic_increasing)

    # 4) 日付の飛び（営業日ベースで極端に長い空白）
    if isinstance(df.index, pd.DatetimeIndex) and n > 1:
        gaps = df.index.to_series().diff().dt.days.dropna()
        report["max_gap_days"] = int(gaps.max())
        report["gaps_over_7d"] = int((gaps > 7).sum())

    # 5) 異常リターン（分割・データグリッチの検出）
    price = df[price_col].dropna()
    if len(price) > 2:
        ret = price.pct_change().dropna()
        report["max_daily_return"] = float(ret.max())
        report["min_daily_return"] = float(ret.min())
        # ±50%超の日次変化は分割かグリッチの疑い
        suspect = ret[(ret > 0.5) | (ret < -0.5)]
        report["suspect_jumps"] = {
            str(d.date()): round(float(v), 3) for d, v in suspect.items()
        }
        # スパイク＆即日反転（1日だけの誤値）の検出
        rev = ((ret < -0.4) & (ret.shift(-1) > 0.6)) | ((ret > 0.6) & (ret.shift(-1) < -0.4))
        report["spike_and_revert"] = int(rev.sum())

    # 6) 非正・ゼロ価格
    report["nonpositive_price"] = int((df[price_col] <= 0).sum())

    return report


def format_report(report: dict) -> str:
    """監査レポートを人間可読の文字列に整形し、警告に印をつける。"""
    lines = ["データ監査レポート", "=" * 40]
    lines.append(f"行数: {report.get('n_rows')}")

    miss = report.get("missing_by_col", {})
    total_missing = sum(miss.values())
    mark = "⚠️ " if total_missing else "○ "
    lines.append(f"{mark}欠損値合計: {total_missing}  {miss if total_missing else ''}")

    dup = report.get("duplicate_index", 0)
    lines.append(f"{'⚠️ ' if dup else '○ '}重複インデックス: {dup}")

    mono = report.get("index_monotonic_increasing", True)
    lines.append(f"{'○ ' if mono else '⚠️ '}日付が単調増加: {mono}")

    if "max_gap_days" in report:
        g = report["gaps_over_7d"]
        lines.append(f"{'⚠️ ' if g else '○ '}7日超の空白: {g}回（最大{report['max_gap_days']}日）")

    if "suspect_jumps" in report:
        sj = report["suspect_jumps"]
        lines.append(f"{'⚠️ ' if sj else '○ '}±50%超の異常日次変化: {len(sj)}件 {sj if sj else ''}")
        sr = report.get("spike_and_revert", 0)
        lines.append(f"{'⚠️ ' if sr else '○ '}スパイク＆即日反転（誤値疑い）: {sr}件")
        lines.append(f"   日次リターン範囲: [{report['min_daily_return']:+.3f}, "
                     f"{report['max_daily_return']:+.3f}]")

    np_ = report.get("nonpositive_price", 0)
    lines.append(f"{'⚠️ ' if np_ else '○ '}非正の価格: {np_}")
    return "\n".join(lines)
