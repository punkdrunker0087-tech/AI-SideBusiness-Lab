"""パイプライン全体の実行制御 ―― Data Providers → Validation → Feature
Pipeline → Research Models → Paper Trading → Monitoring を1日単位で回す。

自動発注・ブローカー接続は含まない（このリポジトリの`macro-research/`と
同じ理由で、実運用の自動発注システムとは明確に切り離す）。
"""
import uuid

import pandas as pd

import alerts
import data_provider
import event_log
import feature_pipeline
import model_layer
import monitoring
import paper_trading
import reconciliation


def run_pipeline(symbols: list, range_: str = "2y", train_split: float = 0.7,
                 sim_days: int = 100, seed: int = 0) -> dict:
    """全体のパイプラインを1回実行する（複数銘柄・sim_days日分をシミュレート）。

    実運用では日次バッチとして毎日1回呼ばれる想定。ここでは検証のため
    履歴データの一部を「モデル学習用」、残りを「日次運用のシミュレーション」
    として扱う。
    """
    run_id = str(uuid.uuid4())[:8]
    account = paper_trading.PaperAccount(cash=1_000_000.0, unit_size=100.0, cost_bps=15.0)

    price_data, feature_data, models = {}, {}, {}
    for sym in symbols:
        df = data_provider.fetch(sym, range_=range_, run_id=run_id)
        feats = feature_pipeline.build_features(df["close"], sym, run_id=run_id)

        cut = int(len(df) * train_split)
        train_feats, train_close = feats.iloc[:cut], df["close"].iloc[:cut]
        models[sym] = model_layer.train(train_feats, train_close, seed=seed)

        price_data[sym] = df
        feature_data[sym] = feats

    common_dates = feature_data[symbols[0]].index
    for sym in symbols[1:]:
        common_dates = common_dates.intersection(feature_data[sym].index)
    sim_dates = common_dates[cut:cut + sim_days] if len(common_dates) > cut else common_dates[-sim_days:]

    daily_latencies = []
    for date in sim_dates:
        prices_today = {}
        for sym in symbols:
            if date not in feature_data[sym].index:
                continue
            row = feature_data[sym].loc[date]
            price = float(price_data[sym]["close"].loc[date])
            prices_today[sym] = price

            latency = monitoring.inference_latency_check(models[sym], row)
            daily_latencies.append(latency)

            inference = model_layer.infer(models[sym], row, sym, date, run_id=run_id)
            account.process_signal(sym, inference["signal"], inference.get("confidence"),
                                   price, date, run_id=run_id)

        account.mark_to_market(prices_today, date)

        # 監視・アラート（最新の検証結果に基づく）
        val = data_provider.validate(price_data[symbols[0]], symbols[0], run_id=run_id)
        alerts.run_all_checks(val, account, run_id=run_id)

    recon = reconciliation.full_reconciliation(account, run_id=run_id)

    return {
        "run_id": run_id, "account": account, "reconciliation": recon,
        "avg_inference_latency_ms": sum(daily_latencies) / len(daily_latencies) if daily_latencies else None,
        "n_days_simulated": len(sim_dates),
    }
