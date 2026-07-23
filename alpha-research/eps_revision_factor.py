"""EPS修正率ファクター ―― Point-in-Time財務データによる第1候補。

## 数式化
J-Quantsの`/fins/summary`は、決算短信の種類によって「翌期首の予想EPS」
（`NxFEPS`、通期決算開示時にセットされる）と「当期の予想EPS」
（`FEPS`、四半期決算開示時に更新される）が別の列に分かれて出てくる。
両者を開示日順に連結すると、「ある年度の業績予想が、決算のたびに
どう修正されてきたか」という連続系列になる:

  FY開示 → NxFEPS（新年度の予想が初めてセットされる）
  1Q開示 → FEPS（同じ年度の予想が更新される）
  2Q開示 → FEPS（さらに更新）
  3Q開示 → FEPS（さらに更新）
  FY開示 → NxFEPS（新しい年度の予想に切り替わる＝別ターゲット）

年度の切り替わり（FY開示の`NxFEPS`）は「予想の対象そのものが変わる」
ため、その回だけは修正率の計算対象から除外する（前の年度の最終予想と
新年度の初期予想を比較しても「修正」の意味を持たないため）。

  修正率(t) = (予想EPS(t) − 予想EPS(t−1)) / |予想EPS(t−1)|
  （ただし t が年度切り替わりの開示なら NaN とする）

## Point-in-Time原則
`DiscDate`（開示日）**の翌日から**、その修正率の値を「その時点で市場に
知られていた情報」として扱う。開示日当日を含めない理由: 決算発表が
場中か場後かで当日中に反映できたかが銘柄ごとに異なり、翌日からとする
方が保守的で先読みの余地がない。
"""
import os

import numpy as np
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")


def compute_revision_series(summary_df: pd.DataFrame) -> pd.DataFrame:
    """1銘柄の`/fins/summary`結果から、開示日つきの修正率系列を作る。"""
    df = summary_df.copy()
    if df.empty:
        return pd.DataFrame(columns=["DiscDate", "revision"])
    df["DiscDate"] = pd.to_datetime(df["DiscDate"])
    df = df.sort_values("DiscDate")
    df["forecast"] = pd.to_numeric(df["NxFEPS"], errors="coerce").combine_first(
        pd.to_numeric(df["FEPS"], errors="coerce"))
    is_new_cycle = df["NxFEPS"].notna() & (pd.to_numeric(df["NxFEPS"], errors="coerce").notna())
    df["revision"] = df["forecast"].pct_change()
    df.loc[is_new_cycle, "revision"] = np.nan
    return df[["DiscDate", "revision"]].dropna()


def build_pit_panel(universe_codes: list, trading_dates: pd.DatetimeIndex) -> pd.DataFrame:
    """全銘柄の修正率を、Point-in-Timeで日次パネル化する（先読みなし）。

    各銘柄について、開示日の**翌日**から次の修正イベントの前日まで、
    その修正率の値を横展開する（ステップ関数、`ffill`と同じ考え方）。
    修正イベントがない期間はNaN（横断Zスコア計算時に自然に除外される）。
    """
    panel = pd.DataFrame(index=trading_dates, columns=universe_codes, dtype=float)
    for code in universe_codes:
        path = os.path.join(CACHE_DIR, f"fins_summary_{code}.csv")
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            continue
        try:
            raw = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue
        if raw.empty:
            continue
        rev = compute_revision_series(raw)
        if rev.empty:
            continue
        s = pd.Series(np.nan, index=trading_dates)
        for _, row in rev.iterrows():
            effective_date = row["DiscDate"] + pd.Timedelta(days=1)
            s.loc[s.index >= effective_date] = row["revision"]
        # 次の修正イベントより前は直近値を維持（ステップ関数）だが、
        # 複数イベントがある場合は上のループで新しい値に順次上書きされる
        panel[code] = s
    return panel
