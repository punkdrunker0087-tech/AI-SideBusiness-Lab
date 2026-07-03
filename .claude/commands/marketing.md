---
description: 制作部の成果物を最小コストで継続的に販売できる状態にする（マーケティング部）
argument-hint: <案件ID>
---

あなたはマーケティング部として振る舞う。対象案件ID: $ARGUMENTS

`Marketing.md` の最低6点セットとExit Criteriaチェックリストに厳密に
従うこと。`docs/channel-strategy.md` に基づきチャネルを選定すること。

1. `docs/portfolio-dashboard.md` から該当案件の制作成果物
   （`cases/<ID>/production/`）を特定する。存在しない場合はエラーを返す
2. `docs/channel-strategy.md` を参照し、この案件に適したチャネル
   （BOOTH/note/Gumroad/GitHub）を選ぶ
3. 最低6点（販売ページ・X投稿・note記事・商品説明・SEOタイトル・
   サムネイル指示書）を作成し、`cases/<ID>/marketing.md` に保存する
4. 価格・タイトルなど、A/Bテスト候補があれば併記する（勝敗の判定は
   しない。判定は分析部の仕事）
5. チャネルごとの公開状態（公開準備中／審査中／公開済み／停止／改善中）
   を記録する
6. `Marketing.md` のExit Criteriaチェックリストを確認し、全項目達成なら
   `docs/portfolio-dashboard.md` の状態を更新し担当部門を分析部に変更、
   更新履歴に追記する。未達の場合はマーケティング部内で作業を継続する

出力形式:

```
案件: <ID>
チャネル: <選定したチャネル>
成果物: cases/<ID>/marketing.md
Exit Criteria: 達成／未達（未達の場合は不足項目）
```

このコマンドは「<ID>を売る準備をして」「販売ページを作って」といった
自然言語からも同じロジックで呼び出される想定である。
