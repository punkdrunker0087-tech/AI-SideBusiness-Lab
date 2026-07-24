"""ウォーレン・バフェットのバリュー投資 ―― 現代データへの翻訳。

Frazzini, Kabiller & Pedersen (2018) "Buffett's Alpha"（AQR Capital
Management、Financial Analysts Journal）は、バフェット/バークシャーの
長期リターンを、伝統的リスク・ファクターに対する回帰で分解した学術研究。
結論: バフェットの「アルファ」は、**安全性(Betting-Against-Beta)**と
**クオリティ(Quality-Minus-Junk)**ファクターへのエクスポージャーを
コントロールすると統計的に有意でなくなる。つまりバフェットのリターンは
「魔法」ではなく、**割安・安全・高クオリティな株に、適度なレバレッジ
（推定約1.7倍）をかけ続けた**ことの結果として説明できる、とする。

本モジュールはこの知見を、現代の日本株データで再現する:
  Quality = ROE + 粗利率（財務の健全性）
  Value   = 1/PER + 1/PBR（割安性）
  Safety  = 低ベータ（対ベンチマークの感応度が低い＝安全）
のスコアが高い銘柄を選び、適度なレバレッジを検証する。

⚠️ Quality/Valueは現在のYahoo財務スナップショットに依拠するため、過去
バックテストへの一律適用は先読みバイアスになる（このリポジトリの
`aqm-strategy/quality.py`等と同じ制約）。Safety(ベータ)は価格ベースで
全期間先読みなく計算できる。したがって本モジュールは
**「今日この基準で選んだ銘柄群を、過去5年間保有していたら」という
条件付きの検証**であり、動的な銘柄入替を伴う正式なバックテストではない
点に注意。
"""
import time

import numpy as np
import pandas as pd
import requests

_HEADERS = {"User-Agent": "Mozilla/5.0"}
_QS = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"


def _new_session():
    s = requests.Session()
    s.headers.update(_HEADERS)
    s.get("https://fc.yahoo.com", timeout=10)
    crumb = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10).text
    return s, crumb


def _raw(d, key):
    v = d.get(key)
    return v.get("raw") if isinstance(v, dict) else v


def fetch_fundamentals(symbols: list) -> pd.DataFrame:
    s, crumb = _new_session()
    rows = {}
    for sym in symbols:
        try:
            r = s.get(_QS.format(sym),
                     params={"modules": "financialData,defaultKeyStatistics,summaryDetail",
                            "crumb": crumb}, timeout=15).json()
            res = r["quoteSummary"]["result"][0]
            fd, ks, sd = res.get("financialData", {}), res.get("defaultKeyStatistics", {}), res.get("summaryDetail", {})
            rows[sym] = {
                "trailing_pe": _raw(sd, "trailingPE"), "price_to_book": _raw(ks, "priceToBook"),
                "roe": _raw(fd, "returnOnEquity"), "gross_margin": _raw(fd, "grossMargins"),
            }
            time.sleep(0.05)
        except Exception:  # noqa: BLE001
            rows[sym] = {k: np.nan for k in ["trailing_pe", "price_to_book", "roe", "gross_margin"]}
    return pd.DataFrame(rows).T.astype(float)


def rolling_beta(returns: pd.Series, bench_returns: pd.Series, window: int = 252) -> pd.Series:
    """対ベンチマークのローリングβ（先読みなし・価格ベースで全期間計算可能）。"""
    cov = returns.rolling(window).cov(bench_returns)
    var = bench_returns.rolling(window).var()
    return cov / var


def _robust_z(s: pd.Series) -> pd.Series:
    s = s.clip(s.quantile(0.02), s.quantile(0.98))
    s = s.fillna(s.median())
    sd = s.std()
    return (s - s.mean()) / sd if sd else pd.Series(0.0, index=s.index)


def select_buffett_style(fundamentals: pd.DataFrame, beta_now: pd.Series,
                         top_n: int = 8) -> pd.DataFrame:
    """Quality+Value+Safety(低ベータ)の合成スコア上位を選ぶ（ライブ断面）。"""
    quality = (_robust_z(fundamentals["roe"]) + _robust_z(fundamentals["gross_margin"])) / 2
    value = (_robust_z(1.0 / fundamentals["trailing_pe"].replace(0, np.nan))
            + _robust_z(1.0 / fundamentals["price_to_book"].replace(0, np.nan))) / 2
    safety = _robust_z(-beta_now.reindex(fundamentals.index))
    composite = (quality + value + safety) / 3

    df = pd.DataFrame({"quality": quality, "value": value, "safety": safety,
                       "beta": beta_now.reindex(fundamentals.index), "composite": composite})
    return df.sort_values("composite", ascending=False).head(top_n)


def backtest_concentrated_portfolio(close: pd.DataFrame, selected: list,
                                    leverage: float = 1.0) -> pd.Series:
    """選定銘柄の等ウェイト・ポートフォリオを、指定レバレッジで保有した場合の
    エクイティカーブ（現金部分はノーコストと簡略化）。
    """
    ret = close[selected].pct_change().fillna(0.0)
    port_ret = ret.mean(axis=1) * leverage
    return (1 + port_ret).cumprod()
