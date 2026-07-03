# AI Company OS Template Kit — Claude Code一人経営OS（v1）

Claude Code上で動く「AIが会社を運営するOS」の設計一式です。CEO・PM
（COO）・市場調査部・検証部・事業評価部・制作部という役職をAIエージェント
として定義し、会社の憲法（CLAUDE.md）から契約書、意思決定フレームワーク、
実行可能な10個のスラッシュコマンドまでを、実際に週末に副業アイデアを
2件（動画要約サービス／テンプレート販売）検証運用した実例つきで収録して
います。

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
