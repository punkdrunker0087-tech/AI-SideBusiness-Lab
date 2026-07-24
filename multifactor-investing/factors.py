"""3. ファクター定義 ―― 5大ファクターの構築（将来情報混入に注意）。

| ファクター | 着目点 | 定義 |
|---|---|---|
| Value        | 割安性     | 1/PER, 1/PBR（益回り・簿価/株価が高いほど割安） |
| Momentum     | トレンド   | 12ヶ月-1ヶ月モメンタム（直近1ヶ月を除外＝反転効果を避ける学術的標準） |
| Quality      | 財務健全性 | ROE・粗利率 |
| Size         | 時価総額   | −log(時価総額)（小型ほど高スコア＝SMBの向き） |
| LowVol       | 価格変動   | −実現ボラティリティ（低ボラほど高スコア） |

⚠️ 重要な区別:
  - Momentum・LowVol は**価格の時系列**から計算するため、全期間にわたり
    先読みなしで構築できる（`shift`/`rolling`のみ使用）。
  - Value・Quality・Size は Yahoo の**現在スナップショット**（`data_util.
    fetch_fundamentals`）にしか依拠できず、過去へ一律適用すると先読み
    バイアスになる。ライブのクロスセクション比較にのみ正当に使える
    （`../aqm-strategy/quality.py` と同じ制約）。
"""
import numpy as np
import pandas as pd


# --- 価格ベース（全期間で先読みなく構築可能） ---
def momentum_12_1(close: pd.DataFrame) -> pd.DataFrame:
    """12ヶ月-1ヶ月モメンタム: (P[t-21] / P[t-252]) - 1。直近1ヶ月は反転効果を
    避けるため除外する（Jegadeesh & Titman (1993) 以来の学術的標準）。
    """
    return close.shift(21) / close.shift(252) - 1


def low_vol(close: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """低ボラティリティ・スコア = −実現ボラ（高いほど低ボラ＝高スコア）。"""
    logret = np.log(close / close.shift(1))
    rv = logret.rolling(window).std() * np.sqrt(252)
    return -rv


# --- ファンダメンタルベース（現在スナップショット・先読み注意） ---
def value_snapshot(fundamentals: pd.DataFrame) -> pd.Series:
    """Value = z(益回り 1/PER) + z(簿価/株価 1/PBR) の平均。高いほど割安。"""
    earnings_yield = 1.0 / fundamentals["trailing_pe"].replace(0, np.nan)
    book_to_price = 1.0 / fundamentals["price_to_book"].replace(0, np.nan)
    return pd.DataFrame({"ey": earnings_yield, "btp": book_to_price})


def quality_snapshot(fundamentals: pd.DataFrame) -> pd.Series:
    """Quality = ROE・粗利率（高いほど高クオリティ）。"""
    return fundamentals[["roe", "gross_margin"]]


def size_snapshot(fundamentals: pd.DataFrame) -> pd.Series:
    """Size = −log(時価総額)（小型ほど高スコア＝SMBの符号に合わせる）。"""
    return -np.log(fundamentals["market_cap"].replace(0, np.nan))


def build_price_factors(close: pd.DataFrame) -> dict:
    """価格ベースの全期間ファクター（Momentum・LowVol）を返す。"""
    return {"momentum": momentum_12_1(close), "low_vol": low_vol(close)}


def build_snapshot_factors(fundamentals: pd.DataFrame) -> pd.DataFrame:
    """スナップショット・ファクターのZスコアを1つのDataFrameにまとめる（ライブ用）。"""
    def robust_z(s: pd.Series) -> pd.Series:
        s = s.clip(s.quantile(0.02), s.quantile(0.98))
        s = s.fillna(s.median())
        sd = s.std()
        return (s - s.mean()) / sd if sd else pd.Series(0.0, index=s.index)

    value_parts = value_snapshot(fundamentals)
    value_z = (robust_z(value_parts["ey"]) + robust_z(value_parts["btp"])) / 2

    q_parts = quality_snapshot(fundamentals)
    quality_z = (robust_z(q_parts["roe"]) + robust_z(q_parts["gross_margin"])) / 2

    size_z = robust_z(size_snapshot(fundamentals))

    return pd.DataFrame({"value": value_z, "quality": quality_z, "size": size_z})
