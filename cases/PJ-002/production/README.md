# AI Company OS Template Kit
### 「ひとり社長のためのAI経営OS」— An AI Executive Operating System for Solopreneurs（v1）

Claude Code上で動く「社長の経営判断を毎朝支援するAI OS」の設計一式です。
「AIが会社を運営する」のではなく、CEO・PM（COO）・市場調査部・検証部・
事業評価部・制作部という役職をAIエージェントとして定義し、情報収集・
KPI整理・リスク整理・優先順位の提案までをAIが行い、**最終判断は常に
購入者ご自身（人間）が行う**設計です。会社の憲法（CLAUDE.md）から契約書、
意思決定フレームワーク、実行可能な10個のスラッシュコマンドまでを、実際に
週末に副業アイデアを2件（動画要約サービス／テンプレート販売）検証運用
した実例つきで収録しています。

> **本製品はAI（Claude／Anthropic社の生成AIモデル）によって設計・生成
> されたドキュメント一式です。** 経営判断そのものは人間の購入者が行う
> ことを前提とした「AIエージェントのための設計書」であり、Anthropic社
> による公式提供・公認製品ではありません。

## 含まれるもの（MANIFEST.md参照）

- `CLAUDE.md` — 会社の憲法（ミッション・経営理念・開発原則・組織構造・
  KPI階層・経営原則）
- `CEO.md` / `PM.md` — CEO・PM（COO）エージェント定義
- `Research.md` / `Validation.md` / `Evaluation.md` / `Production.md` —
  市場調査部・検証部・事業評価部・制作部の各エージェント定義
- `docs/department-contracts.md` — 全役職の契約定義（Mission/Inputs/
  Outputs/Authority/Cannot do/KPIs/Exit Criteria/Next Department）
- `docs/decision-framework.md` — 8軸スコアリング・5段階Go/No-Go判定・
  Asset Scoreの意思決定フレームワーク
- `docs/portfolio-strategy.md` — 同時進行数の上限・Portfolio Rule・
  収益ルール
- `docs/commands.md` と `.claude/commands/*.md`（10コマンド） — Claude
  Code上でそのまま動くスラッシュコマンド一式（`/next` `/pm` `/intake`
  `/route` `/research` `/validate` `/evaluate` `/produce` `/portfolio`
  `/review`ほか）
- `docs/portfolio-dashboard.md`（初期状態） / `docs/score-history.md` —
  案件管理テンプレート

## こんな人におすすめ

- Claude Codeで自分だけの「小さな会社」を運営したい人
- 副業・個人開発アイデアの検証プロセスを仕組み化したい人
- AIエージェントに役割・権限・KPIを持たせる設計の実例が欲しい人

## セットアップ

1. ファイル一式を自分のリポジトリのルートに配置する
2. `docs/portfolio-dashboard.md` を初期状態のまま使い始める
3. Claude Code上で `/intake` を実行し、最初の案件を投入する
4. `/pm` `/next` で日次の状況確認、`/review` で週次レビューを行う

## ライセンス

`LICENSE.md` を参照してください（個人・社内利用は許可、ファイル自体の
再配布・転売は禁止）。

## 特定商取引法に基づく表記

日本国内の販路（BOOTH/note等）で販売する場合は `TOKUSHOHO-TEMPLATE.md`
を、販売者本人の実情報で埋めた上でご利用ください。
