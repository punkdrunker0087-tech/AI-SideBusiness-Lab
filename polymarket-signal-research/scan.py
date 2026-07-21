"""複数のPolymarket市場 × 金融商品を総当たりで検証するスキャナ。

単一の組み合わせ(n=1)では、高い相関が出ても偶然と区別できない。
そこで多数の組み合わせを回し、各ペアについて並べ替え検定で
「偶然この相関が出る確率(p値)」を計算する。

さらに重要な視点:
- **多重比較**: M個のペアを試せば、有意水準5%でも平均 0.05×M 個は
  偶然「有意」に見える。だから「有意なペアが何個あったか」を、
  偶然で期待される個数と必ず比較する。
- **ポジティブコントロール**: BTC価格市場 × BTC現物 を必ず1本入れる。
  ここで強い相関が出なければ、ツール自体が壊れている(=他の無相関も信用できない)。

使い方:
  python scan.py                 # 既定の総当たり
  python scan.py --n-perm 500    # 検定の精度を上げる
  python scan.py --save data/scan_results.csv
"""
import argparse
import sys

import numpy as np
import pandas as pd

import analyze
import market_source
import polymarket_source as pm

# 検証する金融商品(日本で合法的に取引できるもの中心)
INSTRUMENTS = {
    "USDJPY=X": "ドル円",
    "^N225": "日経225",
}

# 経済イベント系の市場を拾うためのキーワード(現在アクティブな市場から絞る)
ECON_KEYWORDS = [
    "Fed",
    "interest rate",
    "recession",
    "inflation",
    "CPI",
    "GDP",
    "unemployment",
    "rate cut",
    "rate hike",
]

# ほぼ動かない市場(確率が張り付き)はノイズなので除外する閾値
_MIN_PROB_STD = 0.005
_MIN_POINTS = 50


def _collect_econ_markets(max_markets: int) -> list:
    """現在アクティブな経済関連市場のうち、実際に確率が動いているものを選ぶ。"""
    pool = pm.search_markets(keyword="", limit=500)  # 出来高順・未解決市場
    seen = set()
    candidates = []
    for m in pool:
        q = m.question.lower()
        if not any(k.lower() in q for k in ECON_KEYWORDS):
            continue
        if m.yes_token_id in seen:
            continue
        seen.add(m.yes_token_id)
        candidates.append(m)
    candidates.sort(key=lambda m: m.volume_usd, reverse=True)

    picked = []
    for m in candidates:
        if len(picked) >= max_markets:
            break
        try:
            hist = pm.price_history(m.yes_token_id, interval="1m", fidelity=60)
        except Exception:  # noqa: BLE001
            continue
        probs = [x["p"] for x in hist if x.get("p") is not None]
        if len(probs) < _MIN_POINTS or np.std(probs) < _MIN_PROB_STD:
            continue  # 変動のない市場はスキップ
        picked.append(m)
    return picked


def _btc_control():
    """BTC価格市場(アット・ザ・マネー付近)を対照実験として返す。"""
    try:
        markets = pm.search_events("Bitcoin above", limit=10)
    except Exception:  # noqa: BLE001
        return None
    # 確率が0/1に張り付いていない = アット・ザ・マネー付近の市場を選ぶ
    best = None
    for m in markets:
        try:
            hist = pm.price_history(m.yes_token_id, interval="1d", fidelity=10)
        except Exception:  # noqa: BLE001
            continue
        if not hist:
            continue
        last_p = hist[-1].get("p", 0)
        # 0.1〜0.9 の範囲にある(動きのある)市場を優先
        if 0.1 < last_p < 0.9:
            best = m
            break
    return best


def _analyze_pair(poly_hist, mkt_hist, freq, max_lag, n_perm):
    df = analyze.align(poly_hist, mkt_hist, freq=freq)
    if len(df) < max_lag * 2 + 5:
        return None
    obs, pval = analyze.permutation_pvalue(df, max_lag=max_lag, n_perm=n_perm)
    best_lag, best_corr = analyze._best_lag_corr(
        df["prob"].diff().to_numpy(),
        np.log(df["price"]).diff().to_numpy(),
        max_lag,
    )
    return {
        "n": len(df),
        "best_lag": best_lag,
        "best_corr": best_corr,
        "pvalue": pval,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Polymarketシグナル総当たりスキャン")
    p.add_argument("--max-markets", type=int, default=6, help="経済市場の最大数")
    p.add_argument("--max-lag", type=int, default=12, help="相互相関の最大ラグ(時間)")
    p.add_argument("--n-perm", type=int, default=300, help="並べ替え回数")
    p.add_argument("--freq", default="1h", help="整列グリッド間隔")
    p.add_argument("--alpha", type=float, default=0.05, help="有意水準")
    p.add_argument("--save", default="", help="結果CSVの保存先")
    args = p.parse_args()

    print("経済イベント市場を収集中…")
    markets = _collect_econ_markets(args.max_markets)
    print(f"  → {len(markets)}市場")
    for m in markets:
        print(f"     {m.volume_usd/1e6:5.1f}M | {m.question[:55]}")

    print("\nポジティブコントロール(BTC市場)を選定中…")
    btc = _btc_control()
    if btc:
        print(f"  → {btc.question[:55]}")
    else:
        print("  → 見つからず(対照実験なしで続行)")

    # ペアを構築
    jobs = []  # (label, poly_market, symbol, sym_name, is_control, poly_kwargs, mkt_kwargs)
    for m in markets:
        for sym, name in INSTRUMENTS.items():
            jobs.append((m, sym, name, False))
    if btc:
        jobs.append((btc, "BTC-USD", "BTC現物", True))

    print(f"\n{len(jobs)}ペアを検定中(並べ替え{args.n_perm}回/ペア)…\n")
    rows = []
    for m, sym, name, is_ctrl in jobs:
        # 対照実験(BTC)は日内で細かく、経済市場は1ヶ月・1時間で見る
        if is_ctrl:
            poly_hist = pm.price_history(m.yes_token_id, interval="1d", fidelity=10)
            mkt_hist = market_source.price_history(sym, range_="5d", interval="15m")
            freq = "15min"
        else:
            poly_hist = pm.price_history(m.yes_token_id, interval="1m", fidelity=60)
            mkt_hist = market_source.price_history(sym, range_="1mo", interval="1h")
            freq = args.freq
        try:
            res = _analyze_pair(poly_hist, mkt_hist, freq, args.max_lag, args.n_perm)
        except Exception as e:  # noqa: BLE001
            print(f"  skip [{m.question[:30]} × {name}]: {e}")
            continue
        if res is None:
            continue
        tag = " [対照]" if is_ctrl else ""
        rows.append(
            {
                "market": m.question[:45],
                "instrument": name,
                "control": is_ctrl,
                **res,
            }
        )
        print(
            f"  {m.question[:35]:35s} × {name:7s}{tag} | "
            f"lag={res['best_lag']:+d} corr={res['best_corr']:+.3f} "
            f"p={res['pvalue']:.3f} (n={res['n']})"
        )

    if not rows:
        print("\n有効な結果がありませんでした。")
        sys.exit(1)

    df = pd.DataFrame(rows).sort_values("pvalue").reset_index(drop=True)
    real = df[~df["control"]]
    n_tests = len(real)
    n_sig = int((real["pvalue"] < args.alpha).sum())
    # エッジになるのは「Polymarketが先行(best_lag>0)」かつ有意なペアだけ。
    # best_lag<=0(金融商品が先行/同時)は、たとえ有意でも予測には使えない。
    edge = real[(real["pvalue"] < args.alpha) & (real["best_lag"] > 0)]
    n_edge = len(edge)
    expected_fp = args.alpha * n_tests

    print("\n" + "=" * 64)
    print("結果サマリー(p値の小さい順)")
    print("=" * 64)
    print(df.to_string(index=False))

    print("\n" + "-" * 64)
    print(
        f"経済市場ペア: {n_tests}件中 p<{args.alpha} は {n_sig}件"
        f"(偶然の期待値 ≈ {expected_fp:.1f}件)。"
    )
    print(
        f"うち『Polymarketが先行(lag>0)』の有意ペア = {n_edge}件"
        "  ← エッジ候補はこれだけ"
    )
    if n_edge == 0:
        print(
            "→ **予測力の証拠なし。** 有意なペアがあっても方向が逆"
            "(金融商品がPolymarketに先行/同時)で、取引エッジにはならない。"
        )
    elif n_edge <= expected_fp:
        print(
            "→ エッジ候補はあるが、偶然の期待値以下。ほぼ偶然と考えるのが妥当。"
        )
    else:
        print(
            "→ 偶然の期待値を上回るエッジ候補あり。ただし断定は禁物。"
            "別期間で再現するか必ず追試すること(相関≠利益・取引コスト未考慮)。"
        )
    ctrl = df[df["control"]]
    if not ctrl.empty:
        c = ctrl.iloc[0]
        print(
            f"対照実験(BTC): corr={c['best_corr']:+.3f} p={c['pvalue']:.3f} "
            f"lag={c['best_lag']:+d} → "
            + (
                "強い相関を検出。パイプラインは正常に機能している。"
                if abs(c["best_corr"]) > 0.3
                else "相関が弱い。データ期間・粒度を見直すこと。"
            )
        )

    if args.save:
        df.to_csv(args.save, index=False)
        print(f"\n結果を保存: {args.save}")


if __name__ == "__main__":
    main()
