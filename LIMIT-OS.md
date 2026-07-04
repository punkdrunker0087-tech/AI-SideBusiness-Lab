# LIMIT-OS.md — LIMIT LAB Operating System

LIMIT LAB Operating System（LIMIT OS）は、LIMIT LABという会社を実際に
動かす「業務システム」である。理念（Why）・組織（Who）・ワークフロー
（How）・ナレッジ（What）を1つのOSとしてつなぐことで、事業が増えても
判断基準がぶれない土台にする。個々の詳細は各ドキュメントに委ね、本文書は
それらを結びつける地図として機能する。

---

## Why — なぜ存在するか

- **`CONSTITUTION.md`** — LIMIT LAB憲法。Purpose（存在意義）・Mission・
  Vision・Values（会社の憲法 第一条〜第六条）・AI社員行動原則・
  Mission Check・Value Score・失敗の定義・Brand Guardian（拒否権）。
  すべての判断の最上位規範

## Who — 誰が動かすか

- **`CLAUDE.md`** — 経営ルール。組織構造（CEO・PM（COO）・8部門）、
  KPI階層、経営原則
- **`CEO.md`** / **`PM.md`** — CEO・PM（COO）のエージェント定義
- **`Research.md`** / **`Validation.md`** / **`Evaluation.md`** /
  **`Production.md`** / **`Marketing.md`** — 各部門のエージェント定義
- **`docs/department-contracts.md`** — 全役職の契約（Mission/Inputs/
  Outputs/Authority/Cannot do/KPIs/Exit Criteria/Next Department）
- **`docs/org-expansion-roadmap.md`** — 将来の組織拡張構想（役員層・
  共通本部・専門制作部門）。トリガー条件を満たすまで未導入

## How — どう動くか

- **`docs/opportunity-pipeline.md`** — Idea→Research→Validation→
  Prototype→Pilot→Production→Growthの7ステージ。「売れそう」だけで
  即商品化せず、該当条件下ではプロトタイプ・限定パイロットを挟む
- **発掘フェーズ**: 市場調査部 → 検証部 → 事業評価部 → CEO
  （`docs/decision-framework.md`の8軸スコアリング・Value Score・
  5段階判定）
- **実行フェーズ**: CEO承認 → 法務部 → 制作部（Prototype/Pilotを含む
  場合あり） → マーケティング部 → 分析部 → 改善部 → PM → CEO
- **`docs/portfolio-strategy.md`** — 同時進行数の上限、Portfolio Rule、
  Asset Rule、No Internal Completion（公開≠完了、初回売上まで完了と
  しない）
- **`docs/channel-strategy.md`** — 販売チャネル（BOOTH/note/Gumroad/
  GitHub）とプロモーションチャネル（X）の使い分け、80:20の発信方針
- **`.claude/commands/`** — 上記フローをそのまま実行する15個の
  スラッシュコマンド（`/intake` `/research` `/validate` `/evaluate`
  `/produce` `/marketing` `/morning-brief` 等）
- **`/morning-brief`（CEO Morning Brief）** — CEOが毎朝30秒で経営判断
  できるレポート。CEO Score・Constitution Score・Confidence・今日の
  一手・Risk/Opportunity・Reflection・KPI Tracker・Competitor Watch・
  Content Plannerを1回で生成する

## What — 何を蓄積するか

- **`docs/portfolio-dashboard.md`** — 全案件の状態を一望する唯一の
  真実の源（single source of truth）
- **`docs/daily-metrics.md`** — 日次実績ログ（GitHubスター・
  Xフォロワー・BOOTHお気に入り・売上・CEO Score）。人間報告分のみを正とする
  実績台帳
- **`docs/growth-roadmap.md`** — 90日ロードマップとWeek KPI
- **`docs/brand.md`** / **`docs/product-line.md`** — ブランド・商品
  ライン戦略
- **`cases/<ID>/`** — 案件ごとの実成果物（research/validate/evaluate/
  production/marketing）
- **`knowledge/Lessons Learned/`** — Sprintごとの振り返り
  （Decision Quality・AI Hallucination Check・Time Metrics・
  Reusable Assets）
- **`knowledge/CEO Weekly Review/`** — 週末のCEO定例レビュー
  （今週作ったもの・数字・良かったこと・課題・来週やること）
- **`knowledge/Customer Voice/`** — お客様の声のログ（レビュー・
  お問い合わせ・SNS・DM・要望・クレーム・改善案）。改善部の一次情報源
- **`knowledge/Decision Log/`** — CEOの重要な経営判断とその根拠の記録
  （Go/No-Go・価格改定・戦略転換・Brand Guardian発動等）
- **`knowledge/Institutional Memory/`** — 現場レベルで再利用できる知見
  （効いたPrompt・失敗したWorkflow・CVRの高い販売ページ等）。
  Values「継続的な改善」への貢献
- **`knowledge/Performance Review/`** — 各部門の月次振り返り
  （成果・ミス・改善・次月目標）。同じ失敗を繰り返さないための仕組み
- **`knowledge/Annual Reflection/`** — 年次でPurpose/Visionへの到達度を
  振り返る記録

### レビューの階層（cadence）

| 頻度 | 何を | どこに記録 |
|---|---|---|
| 毎日 | CEO Morning Brief | （記録は`docs/daily-metrics.md`のCEO Score推移） |
| 毎週末 | CEO定例レビュー | `knowledge/CEO Weekly Review/` |
| 毎月末 | AI社員Performance Review | `knowledge/Performance Review/` |
| 毎年 | Annual Reflection | `knowledge/Annual Reflection/` |
| 随時 | 経営判断・組織知の記録 | `knowledge/Decision Log/` / `knowledge/Institutional Memory/` |

---

## 使い方

判断に迷ったら、この順で遡る。

1. `CONSTITUTION.md`（この判断は理念に反していないか）
2. `CLAUDE.md`（この判断は経営ルール・KPI階層に沿っているか）
3. `docs/department-contracts.md` / 各部門`.md`（自分の契約範囲内か）
4. `docs/decision-framework.md` / `docs/portfolio-strategy.md`
   （数値基準・運用ルールは何を指示しているか）

新しいドキュメントを追加する際は、このLIMIT-OS.mdの該当セクション
（Why/Who/How/What）に一行追記し、地図から漏れないようにする。
