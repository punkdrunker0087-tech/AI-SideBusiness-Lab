# SYSTEMATIC EQUITY STRATEGY MEMO

**Project:** AQM-01 (Adaptive Quality Momentum)
**Author:** Systematic Research
**Objective:** Long-term market-neutral alpha generation

> これは特定金融機関の内部戦略の再現ではなく、定量投資で一般に知られる
> モメンタム・クオリティ・ボラティリティ管理・リスク管理の考え方を
> 組み合わせた**研究用のオリジナル戦略設計例**である。

---

## 1. Investment Thesis

**Market Inefficiency**: 市場価格は情報を瞬時に織り込むが、「情報を解釈して
ポジション調整する速度」には遅れがある。特に次の4つは完全には効率化されていない:

- 中期モメンタム
- ボラティリティクラスタリング
- 流動性ショック
- ファンダメンタル改善

戦略は **"Trend × Quality × Liquidity" の交点**だけを取引する。

## 2. Universe

- **Primary**: TOPIX500（理由: 流動性・空売り可能・スプレッドが狭い）
- **除外**: 平均売買代金5億円未満 / 上場30日以内 / ストップ高・安連続

## 3. Signal Generation

- リターン: `R_t = ln(P_t / P_{t-1})`
- Momentum: `M = P_t / SMA_120(P_t) − 1`
- Volatility: `σ = sqrt(252) × std(R_20)`
- Quality: `Q = (ROE + GrossMargin − CapitalIntensity) / 3`
- Liquidity: `L = log(Volume × Price)`
- **Composite Score**: `Score = 0.40·Z(M) + 0.25·Z(Q) − 0.20·Z(σ) + 0.15·Z(L)`
- Signal: `Long if Score > 1.5 / Short if Score < −1.5`

## 4. Entry Rules

`Score > 1.5` AND `20DMA > 60DMA` AND `RSI < 70` AND `Volume > 20DMA Volume`
（Shortは逆条件）

## 5. Exit Rules

- Take Profit: `Entry + 3·ATR`
- Stop: `Entry − 2·ATR`
- Time Stop: 20営業日
- Signal Exit: `Score < 0.5`

## 6. Position Sizing

- Inverse Volatility: `Weight_i = (1/σ_i) / Σ_j(1/σ_j)`
- Risk Budget: 1取引 0.5% / VaR 99%
- Kelly Fraction: `f = 0.25 · μ/σ²`（安全係数25% = Quarter-Kelly）

## 7. Risk Framework

| 項目 | 制限 |
|---|---|
| Single Position | 2% NAV |
| Sector | 20% |
| Gross Exposure | 150% |
| Net Exposure | ±10% |
| Daily VaR | 1.5% |
| Expected Drawdown | 10% |
| Max Drawdown | 15% |
| Portfolio Correlation | < 0.4 |
| Market Beta | ≈ 0 |

## 8. Backtest

- 期間: 2010〜現在
- Walk Forward: Train 36ヶ月 / Test 12ヶ月 / Rolling 毎月更新
- Transaction Cost: Commission 5bps / Slippage 10bps / Short Borrow 考慮
- Monte Carlo: 1000回 Bootstrap
- Stress Test: COVID(2020) / Lehman(2008) / 2022利上げ

## 9. Benchmark

- Primary: TOPIX / Secondary: Market Neutral Index
- Metrics: Annual Return / Sharpe / Sortino / Calmar / Hit Rate /
  Profit Factor / Turnover / Capacity / Tracking Error / Information Ratio

## 10. Edge Monitoring

- 毎日監視: Rolling Sharpe / Rolling WinRate / Turnover / Exposure / Drawdown / Capacity
- 統計監視: CUSUM / Page-Hinkley / KS Test / Population Stability Index
- 停止条件: Rolling Sharpe < 0 が3ヶ月継続 / Information Ratio が50%低下 /
  p-value < 0.01 の Structural Break

### Pseudocode

```
for stock in universe:
    score = (0.40*z(momentum(stock)) + 0.25*z(quality(stock))
             - 0.20*z(volatility(stock)) + 0.15*z(liquidity(stock)))
    if score > 1.5:   buy(stock)
    elif score < -1.5: short(stock)
    size = risk_budget(stock)
    stop = entry - 2*ATR
    take = entry + 3*ATR
    monitor()
```

### Expected Characteristics

| 項目 | 目標 |
|---|---|
| Annual Return | 10〜15% |
| Sharpe Ratio | 1.2以上 |
| Max Drawdown | 15%未満 |
| Win Rate | 50〜60% |
| Profit Factor | 1.4以上 |
| Turnover | 150〜250%/年 |

---

## 実装スコープ（この設計を我々の環境で実現する際の現実）

設計は完全でも、**我々が今アクセスできるデータには限界がある**。正直に分離する。

### v0 で実装できる（価格・出来高だけで計算可能）

- Momentum `M`、Volatility `σ`、Liquidity `L` の3ファクター
- クロスセクショナルZスコア → 合成スコア → ロング/ショート選別
- 逆ボラティリティ・サイジング、ドルニュートラル、Gross≈150%
- コストモデル（手数料5bps + スリッページ10bps + 空売りコスト）
- ウォークフォワード（ローリングOOS）、レジーム別（年次）評価
- TOPIXベンチマーク比較、対市場ベータ（≈0の確認）

### Qualityデータ源の調査結果（2026-07 実地検証）

| 手段 | 取得可否 | 履歴 | 登録 | バックテスト適性 |
|---|---|---|---|---|
| **Yahoo quoteSummary（crumb方式）** | ✅ 実装済み。全25銘柄でROE・粗利率取得 | ✗ 現在スナップショットのみ | 不要 | ライブ判断○／過去は**先読みバイアス** |
| **J-Quants API（無料プラン）** | 未検証（要登録） | 過去2年・12週遅延 | 要（メール登録） | 点in-timeに近く○（ただし2年） |
| **EDINET API（XBRL）** | 未検証（APIキー要・XBRL解析が重い） | フル履歴 | 要APIキー | ○だが実装コスト大 |
| SimFin / Alpha Vantage | 日本株カバレッジ不明 | - | 要APIキー | 要確認 |

**結論**: Qualityの現在値はYahoo crumbで**登録不要で取得でき、ライブ4ファクター
ランキングは実装済み**（`quality.py` / `run.py --live`）。
過去にわたる正しいQualityはJ-Quants（要登録・2年）が現実的な次の一手。

> ⚠️ ただし本v0の感度分析（`--quality-static`）で、**先読みバイアスありの
> 有利な条件でもQualityは戦略を救わなかった**（下記「実測」）。
> J-Quants統合に進む前に、ユニバース拡大の方が優先度が高い可能性。

### v0 で未実装（追加データ・追加実装が必要）

| 項目 | 不足しているもの | 調達先の候補 |
|---|---|---|
| **過去のQuality `Q`** | 点in-timeの財務履歴 | J-Quants API / EDINET / 有料フィード |
| **正式 Universe** | TOPIX500の正確な構成銘柄・売買代金 | J-Quants / 取引所データ |
| **セクター中立** | 各銘柄の業種分類 | J-Quants / TOPIX-17 |
| VaR・相関・ベータ上限の逐次制約 | ポートフォリオ最適化層 | （実装課題） |
| ATRベースの個別Entry/Exit（4-5節） | 執行層（本v0はポートフォリオ型で構築） | （設計判断） |
| Monte Carlo / 構造変化検知（8,10節） | ブートストラップ・CUSUM等 | （実装課題） |

### Quality欠落の扱い（重要）

Qualityが取得できないため、v0では **`Q`の重み0.25を残り3ファクターへ
比率保持で再配分**する（`M:σ:L = 0.40:−0.20:0.15` を |重み|和=1 に正規化
→ `M=0.53, σ=−0.27, L=0.20`）。これは**設計の劣化版**であり、
Qualityを入れるまでは「Adaptive **Quality** Momentum」ではなく
「Adaptive Momentum」である点を偽らずに扱う。

> したがって v0 の目的は「AQM-01が儲かるか」を判定することではなく、
> **AQM-01の価格・出来高部分だけでも、コスト後・OOSで市場ニュートラルな
> 正のリターンの兆しがあるか**を、過学習に騙されずに測ること。
