# MANIFEST — AI Company OS Template Kit v1

パッケージに含めるファイルと、リポジトリ内の取得元を対応させる一覧。
実際の配布ZIPを作成する際は、このリストに従ってファイルを収集する。

| パッケージ内パス | 取得元（このリポジトリ内） | 内容 |
|---|---|---|
| CLAUDE.md | /CLAUDE.md | 会社の憲法 |
| CEO.md | /CEO.md | CEOエージェント定義 |
| PM.md | /PM.md | PM（COO）エージェント定義 |
| Research.md | /Research.md | 市場調査部エージェント定義 |
| Validation.md | /Validation.md | 検証部エージェント定義 |
| Evaluation.md | /Evaluation.md | 事業評価部エージェント定義 |
| Production.md | /Production.md | 制作部エージェント定義 |
| docs/department-contracts.md | /docs/department-contracts.md | 全役職の契約定義 |
| docs/decision-framework.md | /docs/decision-framework.md | 意思決定フレームワーク |
| docs/portfolio-strategy.md | /docs/portfolio-strategy.md | ポートフォリオ運用ルール |
| docs/commands.md | /docs/commands.md | コマンド仕様書 |
| docs/score-history.md | /docs/score-history.md | スコア履歴フォーマット |
| docs/portfolio-dashboard.md | cases/PJ-002/production/portfolio-dashboard-template.md | 案件ダッシュボードの初期テンプレート（空の状態） |
| .claude/commands/next.md 他9件 | /.claude/commands/*.md | 実行可能スラッシュコマンド一式（10個） |
| README.md | cases/PJ-002/production/README.md | 製品説明（買い手向け） |
| LICENSE.md | cases/PJ-002/production/LICENSE.md | 利用許諾 |
| TOKUSHOHO-TEMPLATE.md | cases/PJ-002/production/TOKUSHOHO-TEMPLATE.md | 特定商取引法表記テンプレート |

## 注意

- `docs/portfolio-dashboard.md` は本リポジトリでは案件データが入った
  状態のため、配布パッケージには案件一覧を空にした初期テンプレート版
  （`portfolio-dashboard-template.md`）を同梱する
- AI生成率: 本パッケージの全ドキュメントはClaude（Anthropicの生成AI
  モデル）によって設計・生成された。人間による大幅な追記・修正は本
  Sprintの時点では行われていない（AI生成率: 実質100%）
