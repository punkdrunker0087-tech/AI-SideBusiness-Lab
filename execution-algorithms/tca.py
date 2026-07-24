"""執行品質分析（Transaction Cost Analysis）―― 単純な平均価格でなく要素分解する。

Implementation Shortfall（Perold 1988 の考え方）を、
  スプレッドコスト + マーケットインパクトコスト + 遅延コスト + 機会コスト
  + 手数料
に分解する。あわせて約定率・VWAPベンチマーク比較も行う。
"""
from dataclasses import dataclass

import numpy as np

import engine
import market_sim


@dataclass
class TCAReport:
    fill_rate: float
    implementation_shortfall_bps: float
    spread_cost_bps: float
    impact_cost_bps: float
    delay_cost_bps: float
    opportunity_cost_bps: float
    commission_bps: float
    market_drift_bps: float   # 執行期間中の市場そのものの値動き（執行スキルとは無関係）
    vwap_benchmark_bps: float
    avg_exec_price: float
    arrival_price: float


def analyze(result: engine.ExecutionResult, session: market_sim.MarketSession,
           side: int = 1, commission_bps: float = 3.0) -> TCAReport:
    """side: +1=買い, -1=売り。"""
    filled = result.filled
    exec_price = result.exec_price
    total_target = float(np.sum(result.schedule))
    total_filled = float(np.sum(filled))
    fill_rate = total_filled / total_target if total_target else np.nan

    valid = ~np.isnan(exec_price) & (filled != 0)
    if not valid.any() or total_filled == 0:
        return TCAReport(fill_rate, *(np.nan,) * 10, result.arrival_price)

    avg_exec_price = float(np.sum(filled[valid] * exec_price[valid]) / np.sum(filled[valid]))
    arrival = result.arrival_price
    to_bps = lambda x: x / arrival * 1e4 * side  # noqa: E731

    is_bps = to_bps(avg_exec_price - arrival)

    # スプレッドコスト: 支払った半スプレッドの出来高加重平均
    half_spreads = session.spread[valid] / 2.0
    spread_cost_bps = to_bps(np.sum(filled[valid] * half_spreads * side) / np.sum(filled[valid])) if side else 0.0
    spread_cost_bps = float(np.sum(np.abs(filled[valid]) * half_spreads) / np.sum(np.abs(filled[valid]))
                            / arrival * 1e4)

    # マーケットインパクトコスト: 約定価格と「自分のインパクトを除いた市場価格」の差
    market_only = session.mid[valid]
    impact_component = (exec_price[valid] - market_only) * side - spread_cost_bps * arrival / 1e4
    impact_cost_bps = float(np.sum(np.abs(filled[valid]) * impact_component) / np.sum(np.abs(filled[valid]))
                            / arrival * 1e4)

    # 遅延コスト: 執行開始（最初の約定）までに市場が動いた分
    first_idx = int(np.argmax(valid))
    delay_cost_bps = to_bps(session.mid[first_idx] - arrival) if first_idx > 0 else 0.0

    # 機会コスト: 未達数量に対し、セッション終値までの価格変化を機会損失として計上
    unfilled = total_target - total_filled
    end_price = session.mid[-1]
    opportunity_cost_bps = to_bps((end_price - arrival) * (unfilled / total_target)) if total_target else 0.0

    # VWAPベンチマーク: 自分の平均約定価格 対 市場全体のVWAP（乖離をbpsで）
    market_vwap = float(np.sum(session.mid * session.volume) / np.sum(session.volume))
    vwap_benchmark_bps = to_bps(avg_exec_price - market_vwap)

    # 市場ドリフト（残差）: IS - (執行に起因するコスト合計)。
    # 執行期間中の市場そのもののランダムな値動きであり、執行スキルとは無関係。
    # IS単体は到着価格を基準にするため、この残差でIS全体の大半を占めることが多い
    # （ゆえにVWAPベンチマークの方が執行スキルの評価には安定的とされる）。
    attributable = spread_cost_bps + impact_cost_bps + delay_cost_bps + opportunity_cost_bps + commission_bps
    market_drift_bps = is_bps - attributable

    return TCAReport(
        fill_rate=fill_rate,
        implementation_shortfall_bps=is_bps,
        spread_cost_bps=spread_cost_bps,
        impact_cost_bps=impact_cost_bps,
        delay_cost_bps=delay_cost_bps,
        opportunity_cost_bps=opportunity_cost_bps,
        commission_bps=commission_bps,
        market_drift_bps=market_drift_bps,
        vwap_benchmark_bps=vwap_benchmark_bps,
        avg_exec_price=avg_exec_price,
        arrival_price=arrival,
    )


def format_report(name: str, r: TCAReport) -> str:
    return (
        f"[{name}] 約定率={r.fill_rate*100:.1f}%  "
        f"IS={r.implementation_shortfall_bps:+.1f}bps "
        f"(スプレッド{r.spread_cost_bps:+.1f} + インパクト{r.impact_cost_bps:+.1f} "
        f"+ 遅延{r.delay_cost_bps:+.1f} + 機会{r.opportunity_cost_bps:+.1f} "
        f"+ 手数料{r.commission_bps:+.1f} + 市場ドリフト{r.market_drift_bps:+.1f})  "
        f"対VWAP={r.vwap_benchmark_bps:+.1f}bps"
    )
