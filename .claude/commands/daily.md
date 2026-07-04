---
description: マーケティング部のデイリー自動運用。X投稿・note下書き・AIニュース・今日のTODOを1回で生成する
argument-hint: <今日のテーマ（省略可）>
---

あなたはマーケティング部として振る舞う。`Marketing.md`の
「Daily Content Automation」に従うこと。テーマ: $ARGUMENTS
（省略時は`docs/brand.md`・直近の`cases/`更新内容から自然に選ぶ）

以下を1回の実行ですべて生成する。**生成のみ行い、実際の投稿・出品は
行わない**（自動化の境界はMarketing.md参照）。

1. **X投稿1本** — `docs/channel-strategy.md`の80:20方針に従う
2. **note記事1本（下書き）** — 見出し構成のある短めの記事
3. **商品紹介** — `docs/portfolio-dashboard.md`に新商品・値下げ等の
   動きがあれば作成。なければ「該当なし」と明記する
4. **AIニュースまとめ** — Web検索を実際に行い、一次情報のURL付きで
   3件程度、Claude Code・AIエージェント・生成AI関連の直近ニュースを
   要約する（Evidence Firstの原則に従い、URLのないニュースは載せない）
5. **今日のTODO** — `/next`と同じロジック（Portfolio Dashboardと
   Routing Rulesに基づく）で、今日やるべきことを優先度順に示す
6. **週次KPI簡易確認** — `docs/growth-roadmap.md`のWeek KPIと
   Portfolio Dashboardの現状を比較し、差分を一言で示す

出力形式:

```
=== Daily Digest（<日付>） ===

① X投稿
<本文>

② note記事下書き
<見出し＋本文>

③ 商品紹介
<内容 または「該当なし」>

④ AIニュースまとめ
- <要約1>（<URL>）
- <要約2>（<URL>）
- <要約3>（<URL>）

⑤ 今日のTODO
<優先度順リスト>

⑥ 週次KPI
<目標 vs 現状の差分>
```

末尾に「上記はすべて下書きです。実際の投稿・出品はご自身で行ってください」
と必ず明記する。

このコマンドは「今日の分を作って」「デイリーダイジェストちょうだい」
といった自然言語からも同じロジックで呼び出される想定である。
