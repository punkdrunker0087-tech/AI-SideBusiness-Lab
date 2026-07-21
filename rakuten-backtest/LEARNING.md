# アルゴリズム取引 学習ノート

このプロジェクトで「AIがアルゴリズム取引を学ぶ」記録。暗記ではなく、
一次情報・二次情報を調べ、**自分たちのツール（`rakuten-backtest` /
`../polymarket-signal-research`）を批評する基準**として使えるようにまとめる。
出典は各節末尾に置く。

> 貫く姿勢: **アルゴ取引の9割は「戦略作り」ではなく「その戦略が本物か疑うこと」。**
> 派手なロジックより、過学習・コスト・資金管理を正しく扱えるかで勝敗が決まる。

---

## 1. エッジの本質 ―― 希少で、必ず減衰する

- アルゴ取引の利益の源は**市場の非効率（ミスプライス）**。しかしそれは
  competition と crowding で埋まっていくため、**エッジは希少で、見つけても減衰する**。
- 実証研究では、公開・運用されたバックテスト戦略の live 成績は
  **年2〜3%程度ずつ減衰**し、launch 時のレジーム（相場環境）に依存した
  見かけの実力が大半、という報告もある。
- 教訓: 「過去に効いた」は「これから効く」を意味しない。**エッジは賞味期限つき**。

出典: [Why Backtests Decay: Regime Dependence and Crowding](https://harbourfrontquant.substack.com/p/why-backtests-decay-regime-dependence) /
[Why Backtests Lie: Regime Drift](https://www.profitsmasher.com/2026/02/why-backtests-lie-regime-drift.html)

---

## 2. 戦略の型（リテール・日足で現実的なもの）

| 型 | 発想 | リテール日足での現実性 |
|---|---|---|
| トレンド追随（モメンタム/移動平均） | 上昇が続くものに乗る | ○ 実装容易・低頻度。ただし横ばい相場で削られる |
| 平均回帰（逆張り/RSI/BB） | 行き過ぎは戻る | △ レンジで有効・トレンドで大損。損切り必須 |
| 統計的裁定（ペアトレード） | 相関崩れの収束を取る | △ 2銘柄の関係が壊れると死ぬ。要モニタリング |
| マーケットメイク / HFT | 板の内側で稼ぐ | × 遅延・インフラで機関に勝てない。楽天RSSのDDE遅延（数百ms〜数秒）でも不可 |
| イベントドリブン | 決算・指標で動く | △ 情報取得と約定速度の勝負になりがち |

我々の環境（楽天RSS + 日足スイング）に**現実的なのはトレンド追随と平均回帰**。
高頻度は構造的に不可能なので最初から狙わない。

---

## 3. バックテストの科学（最重要）

### 3大バイアス

1. **先読みバイアス（look-ahead）**: 未来の情報で過去の判断をしてしまう。
   → 対策: シグナルは close[t] で決め、リターンは *翌日* に適用（1日ずらす）。
   `backtest.py` は `positions.shift(1)` で対応済み。
2. **生存者バイアス（survivorship）**: 上場廃止・倒産した銘柄を除いた
   「生き残り」だけで検証すると成績が過大評価される。
   → 我々はYahooの現存銘柄を使うため**この罠に既にはまっている**（要留意）。
3. **データスヌーピング / 過学習（overfitting）**: 多数のパラメータ・銘柄を試し、
   偶然良かったものを「発見」と勘違いする。**最大の敵**。
   → 対策は下記「検証の階段」。

### 検証の階段（下に行くほど厳しく・信頼できる）

| 段階 | 内容 | 我々の状況 |
|---|---|---|
| ① 全期間フィット | 全データで最良パラメータ | ✗ これだけは無意味（過学習そのもの） |
| ② 単純 train/test 分割 | 前半で決め後半で検証 | ✓ `run.py` で実装済み（最低ライン） |
| ③ **ウォークフォワード** | 窓をずらし「再最適化→未来で検証」を繰り返す | ✓ `walkforward.py` で実装（**systematic戦略の最低要件**） |
| ④ Deflated Sharpe / 多重検定補正 | 「何回試したか」でSharpeの有意水準を割り引く | △ 未実装（警告のみ）。次の課題 |
| ⑤ 複数レジームでのストレステスト | 上昇/横ばい/暴落 各局面で崩れないか | △ 部分的（期間分割で間接的に見える程度） |

**ウォークフォワードが「唯一意味のあるバックテスト」**と呼ばれるのは、
パラメータ選択自体を「過去だけを見て行う」プロセスに含め、その選択が
未来で通用したかを測るから。単純分割（②）は「後半で検証」しても、
そもそも試すパラメータを人間が全期間を見て選んでいれば漏れが残る。

> 実装メモ: `walkforward.py` は各フォールドでSharpe最大のパラメータを学習窓で
> 選び、次の検証窓（未見）に適用する。**選ばれるパラメータがフォールド毎に
> 乱高下するなら、それ自体が「安定したエッジがない」証拠**（今回の日経ETF・
> SMAクロスがまさにこれ）。

### Deflated Sharpe Ratio（多重検定の水増し補正）

- 素のSharpe比は、**多数の試行から最良を選んだ瞬間に楽観方向へ歪む**。
- Bailey & López de Prado の Deflated Sharpe Ratio は、
  「試行回数・歪度・尖度・サンプル長」で有意水準を調整し、
  そのSharpeが**偶然でないか**を判定する。
- リテールでも発想は使える: **「何パターン試したか」を数え、勝ちが
  その回数で説明できないか自問する**。`polymarket-signal-research/scan.py` の
  「偶然で期待される有意ペア数と比較」は、この考え方の簡易版。

### コスト・スリッページの現実

- 手数料だけでなく**スプレッド・スリッページ・マーケットインパクト**を見込む。
- リテールの現実的な取引コストは片道 **15〜25bps** 程度。流動性が薄いと
  スリッページは1%超もありうる。
- → `backtest.py` / `walkforward.py` の既定コストを **15bps** に引き上げ済み。
  楽天の国内株手数料がゼロコースで0でも、**スプレッド等でコストは0にならない**。

出典: [The 'Walk-Forward' Test](https://www.alphanova.tech/blog/walk-forward-test) /
[Deflated Sharpe Ratio (Bailey & López de Prado)](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) /
[Deflated Sharpe ratio – Wikipedia](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio) /
[The Cost Layer: Why Most Backtests Are Quietly Lying](https://algorithmictoken.substack.com/p/market-structure-lens-1-the-cost) /
[How to Develop a Strategy Without Data Snooping](https://www.fxreplay.com/learn/how-to-develop-a-trading-strategy-without-data-snooping)

---

## 4. リスク管理と資金配分 ―― 破綻の主因はここ

- **正のエッジがあっても、賭け過ぎれば破産する。** 同じシグナルでも
  ポジションサイズ次第で「複利で増える人」と「吹き飛ぶ人」に分かれる。
- **Kelly基準**: 勝率と損益比から最適な賭け率を出す。ただし
  **入力（勝率等）の推定誤差に極端に敏感**で、フルKellyは大きなDDを生む。
  → 実務は **Half-Kelly / Quarter-Kelly**。
- 経験則: **1トレードのリスクは資金の 0.5〜2%** に抑えると、
  100トレード超でも破産確率を5%以下に保ちやすい。5%リスクは危険。
- **最大ドローダウン（DD）を心理的・資金的に耐えられる水準に設計する**こと。
  バックテストの最大DDは、実運用ではさらに悪化しがち。

> 我々のツールは現状「フルロング/ノーポジ（0/1）」の単純建玉で、
> ポジションサイジングは未実装。**実運用前に必ず資金配分ルールを足す**。

出典: [Kelly Criterion: Position Sizing for Algo Traders](https://paperswithbacktest.com/course/kelly-criterion-position-sizing) /
[Money Management via the Kelly Criterion (QuantStart)](https://www.quantstart.com/articles/Money-Management-via-the-Kelly-Criterion/) /
[Risk of Ruin Calculator](https://tradingcolosseum.com/artigos/risk-of-ruin-calculator)

---

## 5. 現実的な期待値

- **リテールのアルゴ戦略の多くは失敗する。** 主因は過学習・コスト過小評価・
  賭け過ぎ・レジーム変化の見落とし。
- **「B&Hに勝てない」は失敗ではない。** 強気相場では「余計なことをせず
  持ち続ける（バイ&ホールド）」が非常に強い。無理に売買するほど負ける。
  アルゴの価値はむしろ**下落局面のDD抑制**に出ることが多い。
- 目指すべきは「一発逆転」ではなく、**コスト後・OOSで・複数銘柄にわたって
  B&Hをわずかでも安定して上回る（特にリスク調整後）**こと。

---

## 6. 我々のツールの自己監査

| 観点 | rakuten-backtest | polymarket-signal-research |
|---|---|---|
| 先読み防止 | ✓ shift(1) | ✓ ラグ整列 |
| 取引コスト | ✓ 既定15bps | － （売買しないので対象外） |
| 単純OOS分割 | ✓ run.py | － |
| ウォークフォワード | ✓ walkforward.py | － |
| 多重検定の補正 | △ 警告のみ（Deflated Sharpe未実装） | ✓ 並べ替え検定＋偶然期待値比較 |
| ポジションサイジング | ✗ 未実装（0/1建玉） | － |
| 生存者バイアス | ✗ 現存銘柄のみ（未対応） | － |
| ポジティブコントロール | △ B&H基準 | ✓ BTC市場×BTC現物 |

### 次の実装ロードマップ（学びを反映）

1. **複数銘柄でのウォークフォワード一括検証**（多重検定を正面から扱う。
   何銘柄で勝ったかを、偶然の期待値と比較する）
2. **Deflated Sharpe 相当の割引**（試行回数でSharpeの有意性を補正）
3. **ポジションサイジング**（Quarter-Kelly / 固定リスク%）とDD制約
4. **レジーム・フィルタ**（例: 200日線の上だけロング）でストレステスト
5. （厳密化）配当込みトータルリターン・生存者バイアス対応データへの移行

---

## 7. 今回の実測から得た教訓（n は小さい・断定しない）

- **日経ETF(1321.T) × SMAクロス（ウォークフォワード）**: OOSで +50.8% と、
  B&H +157.1% に**大敗**。各フォールドで選ばれるパラメータが乱高下しており、
  **安定したエッジの不在**を示唆。
- **トヨタ(7203.T) × モメンタム（ウォークフォワード）**: OOSでB&Hを
  +10.2%pt・Sharpe+0.14 で上回った。ただし**超過Sharpeは小さく**、
  複数銘柄・戦略を試した中の1つ（＝多重検定）である以上、
  **偶然と区別するには他銘柄での再現が必須**。Deflated Sharpe の発想そのもの。
- 総括: 現時点で「これで勝てる」と言える戦略は**まだ無い**。
  だがそれを**過学習に騙されずに確認できる土台**は整った。これが今回の成果。

---

## 8. 学習リソース（次に深掘りするなら）

- **書籍**: Marcos López de Prado『Advances in Financial Machine Learning』
  （過学習・交差検証の決定版）/ Ernest Chan『Algorithmic Trading』
  （リテール寄りの実践）/ Robert Carver『Systematic Trading』（資金管理と規律）
- **論文**: Bailey & López de Prado "The Deflated Sharpe Ratio" (2014)
- **概念の再確認先**: 本ノート各節末尾の出典リンク
