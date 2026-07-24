"""イベント駆動シミュレーション ―― マーケットメイクは実データでなく合成市場で検証する。

⚠️ 無料データには板情報がないため、実際の注文フローは得られない。
Avellaneda-Stoikov (2008) と同じ標準的な設定で合成市場を作る:
  - 仲値: 算術ブラウン運動 dS = σ dW
  - 到着強度: λ(δ) = A・exp(−κ・δ)  （クォートが仲値から離れるδほど約定しにくい）
これにより、クォート戦略・在庫管理・評価指標の**設計と挙動**を検証できる。
実際の収益性は実市場の板・手数料体系・レイテンシに強く依存し、ここでは扱わない。
"""
from dataclasses import dataclass, field

import numpy as np

import inventory as inv_mod
import quoting


@dataclass
class MarketParams:
    sigma: float = 2.0          # 仲値のボラティリティ（1ステップあたり）
    A: float = 140.0            # 到着強度の基準値（δ=0での強度）
    kappa: float = 1.5          # 到着強度の価格感応度
    n_steps: int = 2000
    dt: float = 0.005           # 1ステップの時間（T=n_steps*dt）


@dataclass
class SimResult:
    mid_path: np.ndarray
    inventory_path: np.ndarray
    cash_path: np.ndarray
    pnl_path: np.ndarray
    fills: list = field(default_factory=list)   # {"step","side","price","mid_at_fill"}
    n_bid_fills: int = 0
    n_ask_fills: int = 0


def run(qparams: quoting.QuoteParams, mparams: MarketParams,
       limits: inv_mod.InventoryLimits = None, seed: int = 0) -> SimResult:
    """1回のマーケットメイク・シミュレーションを実行する。"""
    limits = limits or inv_mod.InventoryLimits()
    rng = np.random.default_rng(seed)

    mid = 100.0
    state = inv_mod.InventoryState()
    mid_path = np.empty(mparams.n_steps)
    inv_path = np.empty(mparams.n_steps)
    cash_path = np.empty(mparams.n_steps)
    pnl_path = np.empty(mparams.n_steps)
    fills = []

    for t in range(mparams.n_steps):
        time_remaining = max((mparams.n_steps - t) * mparams.dt, 1e-6)
        avail = inv_mod.quote_availability(state.position, limits)

        q = quoting.make_quotes(mid, state.position, qparams, time_remaining)
        delta_bid = mid - q.bid   # 仲値からの距離（買いクォート）
        delta_ask = q.ask - mid   # 仲値からの距離（売りクォート）

        # 到着強度 → このステップで約定する確率（ポアソン薄化の近似）
        lam_bid = mparams.A * np.exp(-mparams.kappa * delta_bid) if avail["allow_buy_quote"] else 0.0
        lam_ask = mparams.A * np.exp(-mparams.kappa * delta_ask) if avail["allow_sell_quote"] else 0.0
        p_bid_fill = 1 - np.exp(-lam_bid * mparams.dt)
        p_ask_fill = 1 - np.exp(-lam_ask * mparams.dt)

        if rng.random() < p_bid_fill:            # 自分のビッドで買い約定（在庫+1）
            state.position += 1
            state.cash -= q.bid
            state.trade_count += 1
            fills.append({"step": t, "side": "buy", "price": q.bid, "mid_at_fill": mid})
        if rng.random() < p_ask_fill:             # 自分のアスクで売り約定（在庫-1）
            state.position -= 1
            state.cash += q.ask
            state.trade_count += 1
            fills.append({"step": t, "side": "sell", "price": q.ask, "mid_at_fill": mid})

        mid_path[t] = mid
        inv_path[t] = state.position
        cash_path[t] = state.cash
        pnl_path[t] = state.mark_to_market(mid)

        mid += mparams.sigma * np.sqrt(mparams.dt) * rng.normal()

    n_bid = sum(1 for f in fills if f["side"] == "buy")
    n_ask = sum(1 for f in fills if f["side"] == "sell")
    return SimResult(mid_path, inv_path, cash_path, pnl_path, fills, n_bid, n_ask)
