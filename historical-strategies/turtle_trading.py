"""タートルズのトレンドフォロー戦略 ―― Richard Dennis & William Eckhardt (1983)。

原典のルールを可能な限り忠実に実装する（参照: turtletrader.com "The Original
Turtle Trading Rules"）。

- **N（ボラティリティ単位）**: True Rangeの20日指数平滑平均
    TR = max(high-low, |high-前日close|, |low-前日close|)
    N_t = (19・N_{t-1} + TR_t) / 20
- **System 1**: 20日高値ブレイクでエントリー、10日安値でエグジット
  （直前のSystem1シグナルが利益を出していた場合はスキップ＝
  "whipsawフィルター"。ただしそのシグナルを見送って大きく伸びた場合の
  取りこぼしを防ぐため、55日ブレイクは無条件エントリー）
- **System 2**: 55日高値ブレイクでエントリー、20日安値でエグジット
- **ポジションサイズ**: 1ユニット = 資金の1%リスク ÷ N（株数）
- **ストップロス**: エントリーから2N
- **ピラミッディング**: 0.5N有利に動くごとに1ユニット追加、最大4ユニットまで

本実装はロングオンリー・単一銘柄向けの簡略版（原典は先物の多市場分散が前提）。
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr


def compute_n(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """N = True Rangeの指数平滑平均（原典の再帰式: N_t=(19N_{t-1}+TR_t)/20）。"""
    tr = true_range(df)
    n = tr.copy()
    n.iloc[:window] = tr.iloc[:window].expanding().mean()
    for i in range(window, len(tr)):
        n.iloc[i] = (( window - 1) * n.iloc[i - 1] + tr.iloc[i]) / window
    return n


def donchian(df: pd.DataFrame, entry_window: int, exit_window: int) -> pd.DataFrame:
    """エントリー用高値チャネルと、エグジット用安値チャネル（前日までの値、先読み防止）。"""
    entry_high = df["high"].rolling(entry_window).max().shift(1)
    exit_low = df["low"].rolling(exit_window).min().shift(1)
    return pd.DataFrame({"entry_high": entry_high, "exit_low": exit_low})


@dataclass
class TurtleConfig:
    s1_entry: int = 20
    s1_exit: int = 10
    s2_entry: int = 55
    s2_exit: int = 20
    risk_pct: float = 0.01       # 1ユニットあたりのリスク(資金の1%)
    stop_n_mult: float = 2.0       # ストップは2N
    pyramid_step_n: float = 0.5     # 0.5Nごとにピラミッディング
    max_units: int = 4
    use_whipsaw_filter: bool = True


@dataclass
class TurtleResult:
    equity: pd.Series
    position: pd.Series      # 保有株数
    trades: list = field(default_factory=list)  # 個々のクローズ済み建玉


def run_turtle_system(df: pd.DataFrame, config: TurtleConfig = None,
                      initial_equity: float = 10_000_000.0) -> TurtleResult:
    """タートルズ・システムを1銘柄・ロングオンリーでシミュレートする。"""
    config = config or TurtleConfig()
    n = compute_n(df)
    s1 = donchian(df, config.s1_entry, config.s1_exit)
    s2 = donchian(df, config.s2_entry, config.s2_exit)

    equity = initial_equity
    units = []  # [{"entry_price":..., "shares":..., "stop":...}, ...]
    last_s1_signal_won = None  # whipsawフィルター用
    equity_curve, position_curve = [], []
    trades = []

    close = df["close"].values
    dates = df.index

    for i in range(len(df)):
        price = close[i]
        ni = n.iloc[i]
        total_shares = sum(u["shares"] for u in units)

        # --- エグジット判定(既存ユニットのストップ・チャネル逆行) ---
        if units:
            exit_low = s1.iloc[i]["exit_low"] if len(units) <= 2 else s2.iloc[i]["exit_low"]
            stop_hit = price <= units[0]["stop"]
            channel_exit = not np.isnan(exit_low) and price <= exit_low
            if stop_hit or channel_exit:
                pnl = sum((price - u["entry_price"]) * u["shares"] for u in units)
                equity += pnl
                trades.append({"date": dates[i], "exit_price": price, "pnl": pnl,
                              "reason": "stop" if stop_hit else "channel_exit"})
                last_s1_signal_won = pnl > 0
                units = []

        # --- 新規エントリー・ピラミッディング判定 ---
        if not np.isnan(ni) and ni > 0:
            unit_shares = max(1, int((equity * config.risk_pct) / ni))

            if not units:
                s1_break = not np.isnan(s1.iloc[i]["entry_high"]) and price > s1.iloc[i]["entry_high"]
                s2_break = not np.isnan(s2.iloc[i]["entry_high"]) and price > s2.iloc[i]["entry_high"]

                enter = False
                if s2_break:
                    enter = True  # 55日ブレイクは無条件エントリー
                elif s1_break:
                    enter = not (config.use_whipsaw_filter and last_s1_signal_won)

                if enter:
                    stop = price - config.stop_n_mult * ni
                    units.append({"entry_price": price, "shares": unit_shares, "stop": stop, "n": ni})
            elif len(units) < config.max_units:
                last_entry = units[-1]["entry_price"]
                if price >= last_entry + config.pyramid_step_n * units[-1]["n"]:
                    stop = price - config.stop_n_mult * ni
                    units.append({"entry_price": price, "shares": unit_shares, "stop": stop, "n": ni})
                    for u in units:
                        u["stop"] = max(u["stop"], stop)  # 全ユニットのストップを引き上げ

        unrealized = sum((price - u["entry_price"]) * u["shares"] for u in units)
        equity_curve.append(equity + unrealized)
        position_curve.append(sum(u["shares"] for u in units))

    return TurtleResult(
        equity=pd.Series(equity_curve, index=dates),
        position=pd.Series(position_curve, index=dates),
        trades=trades,
    )
