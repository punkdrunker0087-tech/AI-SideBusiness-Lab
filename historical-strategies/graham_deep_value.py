"""Benjamin Graham の Deep Value ―― *The Intelligent Investor* (1949) / *Security Analysis* (1934)。

## ①原典 / ②公式の要約
Grahamの最も定量的なルールは NCAV（Net Current Asset Value）投資法:

  NCAV = 流動資産 − 総負債 − 優先株
  1株あたりNCAV = NCAV / 発行済株式数

株価が 1株あたりNCAVの2/3以下（かつ直近12ヶ月EPSが黒字）であれば
「清算価値以下で事業そのものがタダ同然」とみなして買う、という手法。
"Defensive Investor"向けにはさらに、PBR×PER ≤ 22.5、負債比率が低いこと
なども基準として挙げている（*The Intelligent Investor* 第14章）。

## ③④ 現代データへの数式化（重大な制約）
⚠️ 実装時にYahoo Finance無料quoteSummary APIを検証した結果、
`balanceSheetHistory`モジュールは**日付のみを返し、流動資産・流動負債
などのライン明細を一切含まない**ことを確認した。そのため**Grahamの
正式なNCAV計算はこのデータソースでは不可能**である。

本実装では、精密なNCAVの代わりに、Grahamの"Defensive Investor"基準の
精神（割安・黒字・低負債）に最も近い、取得可能なフィールドだけで
構成した代理指標を使う（**NCAVそのものではない**ことを明記する）:

  Deep Value proxy score = 低PBR順位 + 黒字EPS必須 + 低D/E順位

具体的には:
  - price_to_book が小さいほど良い（Graham流「清算価値に近い」の代理）
  - trailing_eps > 0 を必須条件とする（原典のEPS黒字フィルター）
  - debt_to_equity が小さいほど良い（Defensive Investorの財務健全性基準の代理）
"""
import pandas as pd


def compute_deep_value(fundamentals: pd.DataFrame, require_positive_eps: bool = True) -> pd.DataFrame:
    """PBR・EPS黒字・D/Eから Deep Value proxy スコアを計算する（NCAVの代理）。

    require_positive_eps=False にすると原典のEPS黒字フィルターを外した
    危険なケースを再現できる（赤字企業が「PBRが低いだけ」で紛れ込む）。
    """
    df = fundamentals.copy()
    for col in ["price_to_book", "trailing_eps", "debt_to_equity"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["price_to_book"])
    df = df[df["price_to_book"] > 0]

    if require_positive_eps:
        excluded_n = int((df["trailing_eps"] <= 0).sum())
        df = df[df["trailing_eps"] > 0]
    else:
        excluded_n = 0

    df["rank_pbr"] = df["price_to_book"].rank(ascending=True)
    df["rank_de"] = df["debt_to_equity"].rank(ascending=True, na_option="bottom")
    df["combined_rank"] = df["rank_pbr"] + df["rank_de"]

    df = df.sort_values("combined_rank")
    df.attrs["n_excluded_negative_eps"] = excluded_n
    return df
