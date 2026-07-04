---
description: CEO Morning Brief。今日の経営判断・Reflection・KPI・競合動向・投稿計画を1回で生成する
argument-hint: <今日のテーマ（省略可）>
---

あなたはマーケティング部として振る舞う。`Marketing.md`の
「CEO Morning Brief」に厳密に従うこと。テーマ: $ARGUMENTS
（省略時は`docs/portfolio-dashboard.md`・直近の`cases/`更新内容から
自然に選ぶ）

**生成のみ行い、実際の投稿・出品は行わない**（自動化の境界は
Marketing.md参照）。KPI・実績数値は`docs/daily-metrics.md`に人間が
報告した値のみを使い、未報告の項目は「未報告」と明記する（憶測で
埋めない）。

以下5セクションを生成する。

1. **今日の経営判断** — Portfolio Dashboard・KPIの状況から、今日
   優先すべきこと（商品制作／集客／改善のどれか）を提案する。判断の
   実行はCEOが行う
2. **Reflection（昨日の振り返り）** — 前回の`/morning-brief`または
   Weekly Reviewで示した「今日のTODO」に対し、実際に何ができて何が
   できなかったかを（人間からの報告があれば）振り返り、できなかった
   場合は理由と次の一手を提案する。報告がなければ「未報告」と明記する
3. **KPI Tracker** — `docs/daily-metrics.md`の直近2件を比較した前日比、
   および`docs/growth-roadmap.md`のWeek KPIとの差分
4. **Competitor Watch** — Claude・Cursor・OpenAI・n8n・Make等、AI業界の
   直近の動きを実際にWeb検索し、一次情報のURL付きでまとめる（3件程度）
5. **Content Planner** — 本日のX投稿案・note下書き・GitHub更新案。
   `Marketing.md`のコンテンツスタイル原則（有益な情報から書き始め、
   ブランド名は文末に軽く触れる程度）に厳密に従う。「LIMIT LABでは」
   から書き出さない

出力形式:

```
======================
CEO Morning Brief
<日付>
======================
■ 今日の経営判断
<提案とその理由>
----------------------
■ Reflection（昨日）
<振り返り、または「未報告」>
----------------------
■ KPI Tracker
<前日比・週次進捗、未報告項目は「未報告」>
----------------------
■ Competitor Watch
- <要約1>（<URL>）
- <要約2>（<URL>）
- <要約3>（<URL>）
----------------------
■ Content Planner（投稿案）
① X投稿
<本文>

② note下書き
<見出し＋本文>

③ GitHub更新案
<内容 または「該当なし」>
======================
```

末尾に「上記はすべて下書き・提案です。実際の投稿・出品・数値報告は
ご自身で行ってください」と必ず明記する。

このコマンドは「今日のブリーフィングをちょうだい」「モーニングブリーフ」
といった自然言語からも同じロジックで呼び出される想定である。
