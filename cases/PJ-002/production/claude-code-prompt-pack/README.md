# Claude Code Prompt Pack — LIMIT LAB WORKS（v1）

Claude Code上でそのまま動く、経営管理系スラッシュコマンド15個のセット
です。「AI Company OS Template Kit」（LIMIT LAB WORKS Standard商品）の
中核ロジックのうち、コマンド部分だけを単体で使いたい方向けの入門商品
です。

> 本製品はAI（Claude／Anthropic社の生成AIモデル）によって設計・生成
> されたドキュメント一式です。Anthropic社による公式提供・公認製品では
> ありません。

## 含まれるコマンド（15個）

- `/next` — 今すぐやるべきことだけを優先度順に提示
- `/pm` — 会社全体の状況を一望するホーム画面
- `/intake` — 新規案件の受付
- `/route` — 案件を次工程へ進める
- `/research` — Evidenceベースの調査成果物を作成
- `/validate` — 調査成果物の品質監査（PASS/REWORK）
- `/evaluate` — 8軸スコアリングでGo/No-Go判定
- `/produce` — 成果物の制作
- `/marketing` — 販売ページ・SNS投稿等の生成
- `/portfolio` — 全案件の一覧化
- `/review` — 週次レビューの自動生成
- `/status` — 個別案件の状態確認
- `/search` — 案件の検索
- `/help` — コマンド一覧
- `/ceo` — 経営相談

## 使い方

1. `.claude/commands/` フォルダを、ご自身のClaude Codeプロジェクトの
   ルートに配置する
2. Claude Code上で `/help` を実行し、動作を確認する
3. 必要に応じて各コマンドの内容（対象・出力形式）を自分のプロジェクトに
   合わせて書き換えて使う

これらのコマンドは、`docs/department-contracts.md` や
`docs/decision-framework.md` のような「契約書」を前提に書かれています。
より高度な運用（8軸スコアリング・Quality Gate等）まで含めた完全版は、
Standard商品「AI Company OS Template Kit」をご参照ください。

## ライセンス

`LICENSE.md` を参照してください（個人・社内利用は許可、ファイル自体の
再配布・転売は禁止）。
