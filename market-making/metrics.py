"""評価指標 ―― 単純な損益だけでなく多面的に見る。

- fill_rate            : 約定率（クォートが実際に約定した頻度の代理）
- avg_holding_time     : FIFOで往復（買い→売り）を対応させた平均保有期間
- inventory_stats      : 在庫の変動（標準偏差・最大絶対値）
- pnl_decomposition    : スプレッド収益 vs 逆選択コスト（マークアウト分析）
- risk_adjusted_return : Sharpe相当（1ステップリターンベース）
"""
import numpy as np
import pandas as pd

import simulation


def fill_rate(result: simulation.SimResult) -> dict:
    n = len(result.mid_path)
    return {
        "total_fills": len(result.fills),
        "bid_fills": result.n_bid_fills,
        "ask_fills": result.n_ask_fills,
        "fills_per_1000steps": len(result.fills) / n * 1000,
        "buy_sell_balance": (result.n_bid_fills - result.n_ask_fills) / max(len(result.fills), 1),
    }


def inventory_stats(result: simulation.SimResult) -> dict:
    inv = result.inventory_path
    return {
        "inventory_mean": float(inv.mean()),
        "inventory_std": float(inv.std()),
        "inventory_max_abs": float(np.abs(inv).max()),
        "final_inventory": float(inv[-1]),
    }


def avg_holding_time(result: simulation.SimResult) -> dict:
    """買い約定と売り約定をFIFOで対応させ、保有期間（ステップ数）を求める。"""
    buys = [f["step"] for f in result.fills if f["side"] == "buy"]
    sells = [f["step"] for f in result.fills if f["side"] == "sell"]
    n = min(len(buys), len(sells))
    if n == 0:
        return {"avg_holding_steps": np.nan, "n_round_trips": 0}
    holding = [sells[i] - buys[i] for i in range(n) if sells[i] >= buys[i]]
    if not holding:
        return {"avg_holding_steps": np.nan, "n_round_trips": 0}
    return {"avg_holding_steps": float(np.mean(holding)), "n_round_trips": len(holding)}


def pnl_decomposition(result: simulation.SimResult, markout_steps: int = 50) -> dict:
    """スプレッド収益 vs 逆選択コストのマークアウト分析。

    各約定について、約定後 markout_steps 経過時点の仲値と比較する:
      - 買い約定なのに、その後 仲値が下がった → 逆選択（情報を持つ売り手に負けた）
      - 売り約定なのに、その後 仲値が上がった → 逆選択
    スプレッド収益 = 約定価格が仲値からどれだけ有利だったか（即時の理論値）
    逆選択コスト   = 保有後にその有利さがどれだけ食われたか
    """
    mid = result.mid_path
    n = len(mid)
    spread_pnl, adverse_pnl = [], []
    for f in result.fills:
        t, side, price = f["step"], f["side"], f["price"]
        m0 = f["mid_at_fill"]
        t_future = min(t + markout_steps, n - 1)
        m_future = mid[t_future]
        if side == "buy":
            spread_pnl.append(m0 - price)          # 仲値より安く買えた分（即時の得）
            adverse_pnl.append(m_future - m0)       # 買った後、値上がりすれば追加の得、値下がりなら損
        else:
            spread_pnl.append(price - m0)
            adverse_pnl.append(m0 - m_future)

    return {
        "spread_pnl_per_fill": float(np.mean(spread_pnl)) if spread_pnl else np.nan,
        "adverse_selection_pnl_per_fill": float(np.mean(adverse_pnl)) if adverse_pnl else np.nan,
        "n_fills_analyzed": len(spread_pnl),
    }


def risk_adjusted_return(result: simulation.SimResult, periods_per_year: float = None) -> dict:
    pnl = result.pnl_path
    ret = np.diff(pnl)
    ret = ret[~np.isnan(ret)]
    if len(ret) < 2 or ret.std() == 0:
        return {"sharpe_per_step": np.nan, "total_pnl": float(pnl[-1] - pnl[0])}
    sharpe = ret.mean() / ret.std()
    return {
        "sharpe_per_step": float(sharpe),
        "total_pnl": float(pnl[-1] - pnl[0]),
        "pnl_std": float(ret.std()),
    }


def full_report(result: simulation.SimResult) -> pd.DataFrame:
    """全指標を1枚にまとめる。"""
    rows = []
    for label, d in [
        ("約定", fill_rate(result)),
        ("在庫", inventory_stats(result)),
        ("保有時間", avg_holding_time(result)),
        ("PnL分解", pnl_decomposition(result)),
        ("リスク調整後リターン", risk_adjusted_return(result)),
    ]:
        for k, v in d.items():
            rows.append({"カテゴリ": label, "指標": k, "値": v})
    return pd.DataFrame(rows)
