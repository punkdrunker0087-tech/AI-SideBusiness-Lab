"""コーポレートアクション ―― 株式分割・配当等で時系列の解釈が変わる箇所を検知する。

Yahooのraw close(未調整)とadjclose(分割・配当調整済み)の乖離パターンから、
イベントらしき日を検知する。合併・スピンオフ・上場廃止は価格系列だけからの
自動判別が難しいため、ここでは「分割らしき急変」「配当らしき小さな調整」の
2種類に限定し、それ以外は「要確認」として保守的にフラグを立てるに留める。
"""
import numpy as np
import pandas as pd


def detect_events(df: pd.DataFrame, split_threshold: float = 0.15,
                  dividend_threshold: float = 0.001) -> pd.DataFrame:
    """raw close と adjclose のリターン差から、コーポレートアクション候補日を検出する。

    - close_ret と adjclose_ret が同日に大きく乖離し、|close_ret|が大きい
      （split_threshold超）→ 分割らしき急変（"split_like"）
    - 乖離はあるが|close_ret|が小さい → 配当調整らしき小さな乖離（"dividend_like"）
    - それ以外の乖離 → "unclassified"（要確認。合併・スピンオフ等の可能性）
    """
    if "adjclose" not in df.columns:
        return pd.DataFrame(columns=["date", "close_ret", "adjclose_ret", "diff", "type"])

    close_ret = df["close"].pct_change()
    adj_ret = df["adjclose"].pct_change()
    diff = (close_ret - adj_ret).abs()

    events = []
    for dt, d in diff.items():
        if pd.isna(d) or d < dividend_threshold:
            continue
        cr = close_ret.loc[dt]
        etype = "split_like" if abs(cr) > split_threshold else "dividend_like"
        events.append({
            "date": str(dt.date()) if hasattr(dt, "date") else str(dt),
            "close_ret": float(cr), "adjclose_ret": float(adj_ret.loc[dt]),
            "diff": float(d), "type": etype,
        })
    return pd.DataFrame(events)


def apply_adjustment_policy(df: pd.DataFrame, policy: str = "adjclose") -> pd.Series:
    """分析用の「解釈済み価格」を1系列で返す。

    policy="adjclose": 分割・配当調整済み系列を使う（バックテスト等の標準）。
    policy="raw": 未調整の生値をそのまま使う（コーポレートアクション自体を
    研究対象にする場合など）。
    """
    if policy == "adjclose" and "adjclose" in df.columns:
        return df["adjclose"]
    return df["close"]
