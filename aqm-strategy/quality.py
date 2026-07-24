"""Qualityファクター（現在スナップショット）を Yahoo quoteSummary から取得する。

Yahooの財務モジュールは crumb + cookie 認証で取得できる（署名不要・登録不要）。
取得できるのは **現在の最新スナップショット**であり、過去の点in-time値ではない。

⚠️ 重要（先読みバイアス）:
  この値を過去のバックテストに一律適用すると「今日のROEで過去を取引する」
  ことになり look-ahead bias になる。**正しい用途は「今日のライブ・ランキング」**。
  過去にわたる正しいQualityは J-Quants(2年・要登録) や EDINET(XBRL) が必要
  （README「Qualityデータ源」参照）。

Q = (ROE + GrossMargin − CapitalIntensity) / 3
  - ROE:              financialData.returnOnEquity
  - GrossMargin:      financialData.grossMargins
  - CapitalIntensity: DuPont分解の資産回転率の逆数 = profitMargins / returnOnAssets
                      （資産の重さ。大きいほど資本集約的でQualityにマイナスとしてQへ）
"""
import time

import numpy as np
import pandas as pd
import requests

_QS = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def _new_session() -> tuple:
    s = requests.Session()
    s.headers.update(_HEADERS)
    s.get("https://fc.yahoo.com", timeout=10)
    crumb = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10).text
    return s, crumb


def _raw(d: dict, key: str):
    v = d.get(key)
    return v.get("raw") if isinstance(v, dict) else v


def fetch_components(universe: list) -> pd.DataFrame:
    """各銘柄の ROE / 粗利率 / 資本集約度(代理) を取得する。"""
    s, crumb = _new_session()
    rows = {}
    for sym in universe:
        try:
            r = s.get(
                _QS.format(sym),
                params={"modules": "financialData", "crumb": crumb},
                timeout=15,
            ).json()
            fd = r["quoteSummary"]["result"][0].get("financialData", {})
            roe = _raw(fd, "returnOnEquity")
            gm = _raw(fd, "grossMargins")
            pm = _raw(fd, "profitMargins")
            roa = _raw(fd, "returnOnAssets")
            cap_int = np.nan
            if pm and roa and pm > 0:
                asset_turnover = roa / pm
                if asset_turnover > 0:
                    cap_int = 1.0 / asset_turnover
            rows[sym] = {"roe": roe, "gross_margin": gm, "capital_intensity": cap_int}
            time.sleep(0.05)
        except Exception:  # noqa: BLE001
            rows[sym] = {"roe": np.nan, "gross_margin": np.nan, "capital_intensity": np.nan}
    return pd.DataFrame(rows).T.astype(float)


def _robust_z(s: pd.Series) -> pd.Series:
    """外れ値に強いZスコア。1/99%tileでウィンソライズ→欠損は中央値補完→標準化。"""
    s = s.copy()
    lo, hi = s.quantile(0.01), s.quantile(0.99)
    s = s.clip(lo, hi)
    s = s.fillna(s.median())
    mu, sd = s.mean(), s.std()
    if not sd or np.isnan(sd):
        return pd.Series(0.0, index=s.index)
    return (s - mu) / sd


def quality_zscore(universe: list) -> pd.Series:
    """Qualityの合成Zスコア（銘柄index）。高いほど高クオリティ。

    Q = z(ROE) + z(GrossMargin) − z(CapitalIntensity) を平均して標準化。
    """
    comp = fetch_components(universe)
    z = (
        _robust_z(comp["roe"])
        + _robust_z(comp["gross_margin"])
        - _robust_z(comp["capital_intensity"])
    ) / 3.0
    return _robust_z(z).rename("quality_z")
