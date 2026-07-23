"""候補ファクター群は本当に独立した情報を持っているか ―― 相関行列・PCA・階層クラスタリング。

ユーザーからの指摘: 「材料を増やせば勝つ」は正確ではなく、「独立した
情報源を持つファクターを追加すると改善する」が正確。FXベータ・金利
ベータはどちらも「グローバル金融環境（円安→米金利上昇→輸出株）」
という同じマクロドライバーを見ている可能性があり、単純な相関係数
（0.491）だけでは実態を捉えきれない。

そこで、候補5ファクター{Momentum, LowVol, Liquidity, FX, Rate}の
**実現リターン系列**（日次、先読みなし）について:
  1. 相関行列を計算する
  2. PCA（主成分分析）で、何個の独立した潜在因子で分散の大半を
     説明できるかを調べる（「5個のファクター」ではなく「実質2〜3個の
     共通因子」ではないかを検証）
  3. 階層クラスタリングで、どのファクターが同じクラスタ（同じ情報）に
     属するかを可視化する

これにより、次に追加すべきファクターは「まだ試していない何か」ではなく
「既存のクラスタと異なる、新しい潜在因子を捉えるもの」であるべき、
という設計指針を得る。
"""
import numpy as np
import pandas as pd
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform

import fx_factor as fx
import panel
import rate_factor as rate
from factor_rotation_walkforward import build_factor_scores, factor_standalone_returns


def correlation_matrix(standalone_returns: pd.DataFrame) -> pd.DataFrame:
    return standalone_returns.corr()


def pca_variance_explained(standalone_returns: pd.DataFrame) -> pd.Series:
    """相関行列の固有値分解で、各主成分が説明する分散比率を返す。"""
    corr = standalone_returns.corr().values
    eigvals = np.linalg.eigvalsh(corr)[::-1]  # 降順
    eigvals = np.clip(eigvals, 0, None)
    explained = eigvals / eigvals.sum()
    return pd.Series(explained, index=[f"PC{i+1}" for i in range(len(explained))])


def hierarchical_clusters(standalone_returns: pd.DataFrame) -> dict:
    """相関距離(1-|corr|)で階層クラスタリングし、デンドログラムの結合順を返す。"""
    corr = standalone_returns.corr()
    dist = 1 - corr.abs()
    condensed = squareform(dist.values, checks=False)
    link = hierarchy.linkage(condensed, method="average")
    labels = corr.columns.tolist()
    return {"linkage": link, "labels": labels, "dist": dist}


def print_dendrogram_text(link, labels):
    """簡易テキスト・デンドログラム（結合順と距離を表示）。"""
    n = len(labels)
    cluster_names = {i: labels[i] for i in range(n)}
    for i, row in enumerate(link):
        a, b, dist, _ = row
        name_a = cluster_names[int(a)]
        name_b = cluster_names[int(b)]
        new_name = f"({name_a}+{name_b})"
        cluster_names[n + i] = new_name
        print(f"  結合{i+1}: {name_a}  +  {name_b}   距離={dist:.3f}")


def main():
    print("パネル構築中（15年・225銘柄・キャッシュ利用）…")
    close, volume = panel.build_panel(range_="15y", use_cache=True)
    fx_close = fx.fetch_usdjpy(range_="15y", use_cache=True)
    rate_close = rate.fetch_us10y(range_="15y", use_cache=True)

    scores = build_factor_scores(close, volume, fx_close, rate_close)
    standalone = factor_standalone_returns(close, scores)

    print("\n" + "=" * 78)
    print("① 相関行列（各ファクター単独の日次実現リターン）")
    print("=" * 78)
    corr = correlation_matrix(standalone)
    print(corr.round(3).to_string())

    print("\n" + "=" * 78)
    print("② PCA: 主成分ごとの説明分散比率")
    print("=" * 78)
    explained = pca_variance_explained(standalone)
    print(explained.round(3).to_string())
    cum = explained.cumsum()
    n_effective = int((cum < 0.90).sum()) + 1
    print(f"\n  累積寄与率90%に達するのに必要な主成分数: {n_effective}"
         f"（候補ファクター数は{len(scores)}）")
    print(
        "  ⚠️ この指標だけで判断するのは早計。固有値がなだらかに減衰している"
        "\n  （極端に1〜2個へ集中していない）ため、単純な閾値だけでは"
        "\n  「5個がほぼ独立」に見えてしまうが、下記③のクラスタリングが"
        "\n  より実態を反映する（相関の符号を無視した閾値だけでは、"
        "\n  LowVolのようにFX/Rateと強い負の相関を持つ＝実質同じ軸の"
        "\n  裏返しであるファクターを見逃す）。"
    )

    print("\n" + "=" * 78)
    print("③ 階層クラスタリング（相関距離 1-|corr|、average法）")
    print("=" * 78)
    hc = hierarchical_clusters(standalone)
    print_dendrogram_text(hc["linkage"], hc["labels"])

    print("\n" + "=" * 78)
    print("結論")
    print("=" * 78)
    print(
        "相関行列・PCA・クラスタリングの結果を総合し、次に追加すべき\n"
        "ファクターは「既存クラスタと同じ情報を測るもの」ではなく、\n"
        "「独立した新しい潜在因子を捉えるもの」を優先すべきかを判断する。"
    )


if __name__ == "__main__":
    main()
