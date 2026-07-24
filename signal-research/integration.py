"""7. シグナル統合 ―― 似た情報を重複して使わないように合成する。

複数特徴量を組み合わせる際、相関・情報の重複を確認し、冗長性を排除する。
直交化（既存シグナルで説明できない残差だけを使う）も提供する。
"""
import numpy as np
import pandas as pd

import evaluation
import features as ft


def signal_correlation(feature_z: dict) -> pd.DataFrame:
    """特徴量間の平均クロスセクション相関行列（冗長性の把握）。

    feature_z: {名前: Zスコア済みパネル}。各日の横断相関を平均する。
    """
    names = list(feature_z)
    mat = pd.DataFrame(np.nan, index=names, columns=names)
    for i, a in enumerate(names):
        for b in names[i:]:
            fa, fb = feature_z[a].align(feature_z[b], join="inner")
            cors = []
            for t in fa.index:
                pair = pd.concat([fa.loc[t], fb.loc[t]], axis=1).dropna()
                if len(pair) >= 5:
                    cors.append(pair.iloc[:, 0].corr(pair.iloc[:, 1]))
            c = np.nanmean(cors) if cors else np.nan
            mat.loc[a, b] = mat.loc[b, a] = c
    return mat.astype(float)


def orthogonalize(target_z: pd.DataFrame, base_z: pd.DataFrame) -> pd.DataFrame:
    """target を base で回帰し、残差（baseで説明できない部分）を返す。

    各日、横断回帰 target = α + β·base + ε の ε を新しいシグナルとする。
    既存シグナルと重複しない独自情報だけを取り出せる。
    """
    resid = pd.DataFrame(np.nan, index=target_z.index, columns=target_z.columns)
    for t in target_z.index:
        pair = pd.concat([target_z.loc[t], base_z.loc[t]], axis=1).dropna()
        if len(pair) < 5:
            continue
        y = pair.iloc[:, 0].values
        x = pair.iloc[:, 1].values
        beta = np.cov(x, y)[0, 1] / np.var(x) if np.var(x) > 0 else 0.0
        alpha = y.mean() - beta * x.mean()
        e = y - (alpha + beta * x)
        resid.loc[t, pair.index] = e
    return resid


def combine(feature_z: dict, weights: dict = None) -> pd.DataFrame:
    """Zスコア済み特徴量を重み付き合成（既定は等ウェイト）。"""
    names = list(feature_z)
    weights = weights or {n: 1.0 / len(names) for n in names}
    combined = None
    for n in names:
        term = feature_z[n] * weights.get(n, 0.0)
        combined = term if combined is None else combined.add(term, fill_value=0.0)
    return combined


def ic_weighted_combine(feature_z: dict, fwd_ret: pd.DataFrame) -> pd.DataFrame:
    """各特徴量のIC平均を重みにした合成（効く特徴量を厚く）。負ICは符号反転。"""
    weights = {}
    for n, fz in feature_z.items():
        icm = evaluation.ic_summary(evaluation.ic_series(fz, fwd_ret)).get("ic_mean", 0.0)
        weights[n] = icm
    return combine(feature_z, weights)
