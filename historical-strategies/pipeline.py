"""共通の10段階研究パイプライン ―― 「歴史的投資理論×AI」シリーズの型。

①原典調査 ②論文調査 ③ルール抽出 ④数式化 ⑤Python実装 は各戦略モジュール
（`turtle_trading.py`・`buffett_style.py`・`magic_formula.py`）のdocstring
で個別に行う。⑥バックテスト以降はこのモジュールで共通化する。

⑥バックテスト: 選定銘柄の保有シミュレーション
⑦感度分析: パラメータ（銘柄数・除外ルール等）を変えた時の頑健性
⑧レジーム分析: 強気/弱気で成績がどう変わるか
⑨⑩「機能する市場・破綻する条件」は各戦略のREADME/synthesisで議論する
"""
import numpy as np
import pandas as pd


def backtest_static_selection(close: pd.DataFrame, selected: list, leverage: float = 1.0) -> pd.Series:
    """選定銘柄の等ウェイト・ポートフォリオを保有した場合のエクイティカーブ。

    ⚠️ 点in-timeの財務データが無料では取得できないため、「今日の基準で
    選んだ銘柄群を、過去N年間保有していたら」という条件付きの検証であり、
    毎年ファンダメンタルズを更新して銘柄入替する正式なウォークフォワードではない。
    """
    ret = close[selected].pct_change().fillna(0.0)
    port_ret = ret.mean(axis=1) * leverage
    return (1 + port_ret).cumprod()


def sensitivity_by_n(ranked: pd.DataFrame, close: pd.DataFrame, n_values: list) -> pd.DataFrame:
    """銘柄数(N)を変えたときの最終リターン・ボラ・最大DDへの感応度。"""
    rows = []
    for n in n_values:
        selected = ranked.index[:n].tolist()
        eq = backtest_static_selection(close, selected)
        ret = eq.pct_change().dropna()
        rows.append({
            "N": n, "最終倍率": eq.iloc[-1],
            "年率ボラ": ret.std() * np.sqrt(252),
            "最大DD": (eq / eq.cummax() - 1).min(),
        })
    return pd.DataFrame(rows)


def classify_regime(bench_close: pd.Series, trend_window: int = 60) -> pd.Series:
    ma = bench_close.rolling(trend_window).mean()
    return pd.Series(np.where(bench_close > ma, "強気", "弱気"), index=bench_close.index)


def performance_by_regime(equity: pd.Series, regimes: pd.Series) -> pd.DataFrame:
    ret = equity.pct_change().dropna()
    reg = regimes.reindex(ret.index)
    rows = []
    for label in pd.unique(reg.dropna()):
        sub = ret[reg == label]
        if len(sub) < 10:
            continue
        rows.append({"regime": label, "n_days": len(sub),
                    "年率リターン": sub.mean() * 252, "年率ボラ": sub.std() * np.sqrt(252)})
    return pd.DataFrame(rows).set_index("regime") if rows else pd.DataFrame()
