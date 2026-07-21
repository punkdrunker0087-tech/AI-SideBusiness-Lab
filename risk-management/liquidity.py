"""7. 流動性評価 ―― 「必要なときに現実的に手仕舞えるか」を評価する。

価格が良くても、出来高に対して大きすぎる建玉は解消に時間がかかり、
その間に価格が動くリスクを負う。売買代金・想定売却日数を確認する。
"""
import numpy as np
import pandas as pd


def adv_value(close: pd.Series, volume: pd.Series, window: int = 20) -> float:
    """平均売買代金（直近window日、円）。"""
    return float((close * volume).rolling(window).mean().iloc[-1])


def days_to_liquidate(position_value: float, close: pd.Series, volume: pd.Series,
                      participation: float = 0.10, window: int = 20) -> float:
    """建玉を解消するのにかかる想定日数。

    participation: 1日の出来高のうち自分が占めてよい割合（10%が保守的な目安）。
    """
    adv = adv_value(close, volume, window)
    if adv <= 0:
        return np.inf
    return position_value / (participation * adv)


def liquidity_report(positions_value: pd.Series, close: pd.DataFrame,
                     volume: pd.DataFrame, participation: float = 0.10) -> pd.DataFrame:
    """各銘柄の 売買代金 / 想定売却日数 を一覧化する。"""
    rows = []
    for sym, val in positions_value.items():
        if sym not in close.columns:
            continue
        adv = adv_value(close[sym], volume[sym])
        dtl = days_to_liquidate(abs(val), close[sym], volume[sym], participation)
        rows.append({
            "銘柄": sym,
            "建玉(円)": val,
            "平均売買代金(億円)": adv / 1e8,
            "想定売却日数": dtl,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["流動性注意"] = df["想定売却日数"] > 1.0   # 1日で抜けられないと注意
    return df
