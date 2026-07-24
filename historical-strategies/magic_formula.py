"""Joel Greenblatt の Magic Formula ―― "The Little Book That Beats the Market" (2005)。

## ①原典 / ②公式の要約
「割安（Earnings Yield）」と「高品質（Return on Capital）」の2指標だけで
銘柄を順位付けし、両方の順位合計が良い銘柄を買って1年保有・入替する。

  Earnings Yield = EBIT / Enterprise Value
  Return on Capital (ROC) = EBIT / (Net Working Capital + Net Fixed Assets)

原典は金融株・公益株を対象外とする（資本構成の性質が異なりEV/ROCの
意味が崩れるため）。

## ③④ 現代データへの数式化（近似・要注意）
Yahoo Financeの無料APIはEBIT・正味運転資本・純固定資産を直接提供しない。
以下の近似で代替する（**精密な原典の値ではない**ことを明記する）:

  EBIT_proxy = 売上高 × 営業利益率（operatingMargins）
  Invested Capital_proxy = Enterprise Value − 現金同等物
  Earnings Yield = EBIT_proxy / Enterprise Value
  ROC_proxy = EBIT_proxy / Invested Capital_proxy

実際に8306.T（三菱UFJ、銀行）でEnterprise Valueが**負値**になることを
確認した（predicated on市場の時価総額 − 現金＋負債という単純な計算が
銀行の資本構成では破綻するため）。これは原典が金融株を除外する理由を
まさにデータで裏付ける結果であり、本実装でも金融セクターを除外する。
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


def fetch_magic_formula_inputs(symbols: list) -> pd.DataFrame:
    """EBIT_proxy計算に必要な財務スナップショット＋業種（除外判定用）を取得する。"""
    s, crumb = _new_session()
    rows = {}
    for sym in symbols:
        try:
            r = s.get(_QS.format(sym),
                     params={"modules": "financialData,defaultKeyStatistics,assetProfile",
                            "crumb": crumb}, timeout=15).json()
            res = r["quoteSummary"]["result"][0]
            fd, ks = res.get("financialData", {}), res.get("defaultKeyStatistics", {})
            ap = res.get("assetProfile", {})
            rows[sym] = {
                "total_revenue": _raw(fd, "totalRevenue"),
                "operating_margin": _raw(fd, "operatingMargins"),
                "total_cash": _raw(fd, "totalCash"),
                "enterprise_value": _raw(ks, "enterpriseValue"),
                "sector": ap.get("sector", "不明"),
            }
            time.sleep(0.05)
        except Exception:  # noqa: BLE001
            rows[sym] = {"total_revenue": np.nan, "operating_margin": np.nan,
                        "total_cash": np.nan, "enterprise_value": np.nan, "sector": "不明"}
    return pd.DataFrame(rows).T


EXCLUDED_SECTORS = {"Financial Services", "Financial", "Utilities"}


def compute_magic_formula(inputs: pd.DataFrame, exclude_financials: bool = True,
                         require_positive_values: bool = True) -> pd.DataFrame:
    """Earnings Yield・ROCを計算し、順位合計（小さいほど良い）でランキングする。

    exclude_financials と require_positive_values は意図的に独立させている。
    実装時、両方を1つのフラグに束ねていたところ、Enterprise Value非正の
    銘柄が金融セクター除外の有無に関わらず`require_positive_values`相当の
    チェックで結局弾かれ、「除外あり/なし」の比較が実質的に無意味になる
    バグを発見した。危険なケース（原典の除外ルールを守らず、かつ異常値
    チェックも行わない）を正しく再現するには、両フラグを別々に無効化
    できる必要がある。
    """
    df = inputs.copy()
    for col in ["total_revenue", "operating_margin", "total_cash", "enterprise_value"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if exclude_financials:
        before = len(df)
        df = df[~df["sector"].isin(EXCLUDED_SECTORS)]
        excluded_n = before - len(df)
    else:
        excluded_n = 0

    df["ebit_proxy"] = df["total_revenue"] * df["operating_margin"]
    df["invested_capital_proxy"] = df["enterprise_value"] - df["total_cash"]

    if require_positive_values:
        # ROC・Earnings Yieldとも、Enterprise Valueや投下資本が非正の銘柄は
        # 定義不能として除外する（原典の趣旨に反する異常値を混入させないため）
        valid = (df["enterprise_value"] > 0) & (df["invested_capital_proxy"] > 0)
        df = df[valid]

    df["earnings_yield"] = df["ebit_proxy"] / df["enterprise_value"]
    df["roc"] = df["ebit_proxy"] / df["invested_capital_proxy"]

    df["rank_ey"] = df["earnings_yield"].rank(ascending=False)
    df["rank_roc"] = df["roc"].rank(ascending=False)
    df["combined_rank"] = df["rank_ey"] + df["rank_roc"]

    df = df.sort_values("combined_rank")
    df.attrs["n_excluded_financials"] = excluded_n
    return df
