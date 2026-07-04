# product-line.md — LIMIT LAB WORKS 商品ライン戦略

2026-07-04、CEOはミッションの重心を「AI Company OSを売る」から
「LIMIT LABというブランドを育てる」へ修正した。単発の商品ではなく、
価格帯ごとの商品ラインを用意し、1つの開発資産から複数の商品を生む
（Build Once, Sell Many）ことを基本戦略とする。

さらに同日、ブランドポジショニングを「AIが会社を運営するOS」から
**「ひとり社長のためのAI経営OS」（An AI Executive Operating System for
Solopreneurs）**へ改訂した（詳細は`docs/brand.md`）。商品名の直後に
このサブタイトルを添えることを商品ライン共通のルールとする。

## 価格帯ライン

| ライン | 価格帯 | 役割 | 例 |
|---|---|---|---|
| Starter | ¥300〜¥500 | LIMIT LABを試してもらう入口商品 | Claude Code Prompt Pack、Meeting Template Pack、AI Markdown Template |
| Standard | ¥980〜¥1,980 | 主力商品 | AI Company OS Template Kit、Business Template Factory、AI Workflow Collection |
| Premium | ¥2,980〜¥4,980 | 将来の高単価商品 | AI SideBusiness Lab Complete Edition、Claude Code Automation Bundle、AI Company OS Pro |

## 商品ピラミッド（2026-07-04時点）

```
Premium
Coming Soon
────────────────────
Standard
¥980  AI Company OS Template Kit
────────────────────
Starter
¥480  Claude Code Prompt Pack
¥480  AI Business Template Pack（準備中）
```

## 1つの開発資産から生まれる商品ロードマップ

このプロジェクトの開発過程そのものが商品の源泉になる。以下の順で
切り出す。「買った瞬間に価値が分かる商品」を優先し、玄人向けの商品
（Research Department Prompt等）は後回しにする。

1. **AI Company OS Template Kit**（Standard、公開済み） — 会社OS一式の
   フルパッケージ
2. **Claude Code Prompt Pack**（Starter、公開待ち） — `.claude/commands/`
   のスラッシュコマンド一式を単体商品として切り出したもの
3. **AI Business Template Pack**（Starter、次の商品） — 議事録テンプレート・
   SOP・マニュアル・要件定義・レビューシートなど、仕事ですぐ使える
   実務テンプレート集。玄人向けの設計思想を知らなくても価値が分かる
4. **Research Department Prompt**（Starter〜Standard） — Research.md・
   Validation.md・Evaluation.mdとEvidence First手法を切り出したもの
5. **Marketing Department Prompt**（Starter〜Standard） — Marketing.md・
   channel-strategy.mdと販売ページ/SNS生成の手法を切り出したもの
6. **会社OS完全版**（Premium） — 上記すべて＋実際の運用実績（PJ-001/
   PJ-002のケーススタディ）を含む完全版

## 運用ルール

- 新商品は既存のProduction/Marketingパイプライン（`/produce` `/marketing`）
  でそのまま作る。パイプライン自体の設計変更は伴わない
- 同一案件（PJ-002）配下で複数商品を並行して制作・販売してよい。
  `cases/PJ-002/production/<商品名>/` の形でサブフォルダを分ける
- 価格ラインの目的は「客単価を上げること」ではなく「入口を増やすこと」。
  Starterで接点を作り、Standard・Premiumへの導線とする
