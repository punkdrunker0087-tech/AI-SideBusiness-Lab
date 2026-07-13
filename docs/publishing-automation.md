# publishing-automation.md — 規約を守って公開を自動化する

`knowledge/Decision Log/2026-07-13-no-credentials-boundary.md`の線
（AIに認証情報を渡さない）を守ったまま、公開作業を最大限自動化する
正規ルートをまとめる。要点: **パスワードをAIに渡すのではなく、
プラットフォーム公式の"GitHub連携"を使う。** これは規約違反にならず、
AIは認証情報を一切持たない。

## プラットフォーム別の自動化可否（正直な現状）

| 媒体 | 自動公開 | 方法 | 誰が認証を持つか |
|---|---|---|---|
| **Zenn** | ✅ 完全自動 | 公式のGitHub連携。`articles/`のMarkdownをpush→数十秒で自動公開。`published_at`で予約投稿も可 | CEOがZennダッシュボードでOAuth連携（1回のみ）。AIは一切持たない |
| **Qiita** | ✅ 準自動 | Qiita CLI＋GitHub Actions。CEO自身のアクセストークンで動く | CEOがトークンをGitHub Secretsに置く。AIは見ない |
| **note** | ❌ 不可 | 公式の投稿APIなし。手動貼り付けのみ | — |
| **X** | ⚠️ 手動＋純正予約 | 自動投稿botは規約リスク。純正の予約投稿機能を使う | CEO操作 |

## 確定（2026-07-13）: 専用の公開リポジトリ方式
CEO決定により、会社OSリポジトリとは分離した**公開記事専用のGitHub
リポジトリ**をZennに連携する。内部戦略ドキュメントをZennアプリに
渡さずに済む。以下はその具体手順（CEOが画面で操作）。

## 推奨セットアップ（Zenn・一番効く）

### 一度だけCEOがやること（パスワードは誰にも渡らない）
1. 公開用の**独立したGitHubリポジトリ**を作る（推奨。会社OSの内部
   戦略リポジトリとは分離し、公開記事だけを置く。publicで良い）
   - 簡便策として本リポジトリの`articles/`を連携する手もあるが、内部
     戦略ドキュメントごとZennアプリに読み取り権限を渡すことになるため
     **専用リポジトリ推奨**
2. https://zenn.dev/dashboard/deploys でGitHubリポジトリを連携
   （GitHubのOAuth認可＝CEO本人のクリック。トークン/パスワードをAIや
   第三者に渡す操作は一切ない）
3. リポジトリに`articles/`フォルダを作る

### 以後の運用（作業効率が最大化される形）
1. AIが記事を`articles/<slug>.md`にZennフロントマター付きで書く→commit
2. **レビューは`published: false`のまま**（pushしても公開されない）
3. CEOが内容を承認したら`published: true`に変える（または
   `published_at: 2026-07-15 07:00`で予約）→push→**自動公開**
4. 「公開ボタンを押す」に相当するのは、この1行の変更をpushする瞬間
   だけ。CEOの手作業は実質ゼロに近い

### フロントマターの形（Zenn）
```
---
title: "記事タイトル"
emoji: "🏢"
type: "tech"        # tech（技術）or idea（アイデア/体験）
topics: ["claudecode", "ai", "個人開発"]   # 最大5個
published: false    # 承認後にtrue、または published_at で予約
---
```

## この方式が線引きを守る理由
- AIはGitHubにcommitするだけ（🟢）。認証情報は保持しない
- 公開の可否は`published`フラグ＝**人間の承認**が最終ゲート（🟡）
- 使うのはZenn/Qiita公式機能＝規約違反にならない（🔴のbot自動投稿とは
  別物）
- note/Xのように公式の自動公開がない媒体は、無理に自動化せず手動
  （＝AIは貼り付け一発の完成形まで用意し、人間の操作を数秒に減らす）

## 参考
- Zenn公式: リポジトリ連携（https://zenn.dev/zenn/articles/connect-to-github ）
