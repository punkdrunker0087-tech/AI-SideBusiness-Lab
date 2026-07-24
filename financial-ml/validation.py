"""5. 時系列に配慮した検証 ―― Purge（除去）とEmbargo（禁輸期間）つき walk-forward。

ラベルが「20日先リターン」のように**未来の窓**を参照する場合、単純に
日付で訓練/検証を分割しただけでは情報漏洩が起きる:

  - 訓練データの終盤のサンプルは、そのラベル期間[t, t+horizon]が検証期間に
    食い込んでおり、実質的に検証期間の情報を学習してしまう（要 **Purge**）
  - 検証データ終了直後の期間も、特徴量の自己相関等を通じて検証情報が
    次の訓練へ漏れる可能性がある（要 **Embargo**）

参照: López de Prado, M. (2018) "Advances in Financial Machine Learning"
（Purged K-Fold CV・Embargoの提唱）
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Fold:
    train_idx: np.ndarray
    test_idx: np.ndarray
    train_range: tuple
    test_range: tuple
    n_purged: int


def purged_walk_forward(df: pd.DataFrame, date_col: str, horizon_days: int,
                        n_splits: int = 4, embargo_days: int = 5) -> list:
    """日付順にn_splits+1個のブロックへ分け、逐次 train→test のフォールドを作る
    （拡大窓・expanding window）。

    各フォールドについて:
      - train = そのブロック以前の全データ（過去にtestとして使ったブロックも
        次のフォールドでは訓練データに繰り入れる＝拡大窓）から、
        ラベル期間がtest開始日に食い込む分をPurgeで除去
      - embargo_days = Purgeでの除去に加え、test直前にさらに設ける安全マージン
        （train/testの境界でのわずかな系列相関からの漏洩に備える追加の余白）

    注意: embargoは「testの直前」にのみ適用する。過去のブロック全体を
    testブロック終了時点基準でフィルタするのは誤りで、拡大窓のtrainデータを
    全滅させてしまう（本実装で実際に踏んだ罠。テストで検出・修正済み）。
    """
    dates = pd.to_datetime(df[date_col]).values
    unique_dates = np.sort(pd.unique(dates))
    blocks = np.array_split(unique_dates, n_splits + 1)

    folds = []
    for i in range(1, len(blocks)):
        test_dates = blocks[i]
        test_start, test_end = test_dates[0], test_dates[-1]

        train_dates_pool = np.concatenate(blocks[:i])
        cutoff = test_start - np.timedelta64(horizon_days + embargo_days, "D")
        train_dates = train_dates_pool[train_dates_pool <= cutoff]
        n_purged = len(train_dates_pool) - len(train_dates)

        train_idx = df.index[pd.to_datetime(df[date_col]).isin(train_dates)].to_numpy()
        test_idx = df.index[pd.to_datetime(df[date_col]).isin(test_dates)].to_numpy()

        folds.append(Fold(
            train_idx=train_idx, test_idx=test_idx,
            train_range=(str(pd.Timestamp(train_dates.min()).date()) if len(train_dates) else None,
                        str(pd.Timestamp(train_dates.max()).date()) if len(train_dates) else None),
            test_range=(str(pd.Timestamp(test_start).date()), str(pd.Timestamp(test_end).date())),
            n_purged=n_purged,
        ))
    return folds


def naive_walk_forward(df: pd.DataFrame, date_col: str, n_splits: int = 4) -> list:
    """比較用: Purge/Embargoなしの単純な時系列分割（漏洩がありうる悪い例）。"""
    dates = pd.to_datetime(df[date_col]).values
    unique_dates = np.sort(pd.unique(dates))
    blocks = np.array_split(unique_dates, n_splits + 1)

    folds = []
    for i in range(1, len(blocks)):
        test_dates = blocks[i]
        train_dates = np.concatenate(blocks[:i])
        train_idx = df.index[pd.to_datetime(df[date_col]).isin(train_dates)].to_numpy()
        test_idx = df.index[pd.to_datetime(df[date_col]).isin(test_dates)].to_numpy()
        folds.append(Fold(
            train_idx=train_idx, test_idx=test_idx,
            train_range=(str(pd.Timestamp(train_dates.min()).date()),
                        str(pd.Timestamp(train_dates.max()).date())),
            test_range=(str(pd.Timestamp(test_dates[0]).date()), str(pd.Timestamp(test_dates[-1]).date())),
            n_purged=0,
        ))
    return folds
