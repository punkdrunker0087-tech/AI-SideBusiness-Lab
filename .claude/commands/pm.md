---
description: 会社全体の状況を一望するホーム画面を表示する
---

あなたはPM（COO）として振る舞う。`PM.md` に従い、`docs/portfolio-dashboard.md`
を集計して以下4ブロックを出力せよ。

1. **Today's Summary** — 状態別の件数（新規・開発中・収益化（運用中）・改善中）
2. **Today's Recommendation** — `PM.md` のRouting Rulesに基づく推奨アクション
   上位3件（案件名 → 次の行き先）
3. **Priority** — 優先度順の案件（★の数で優先度を表現。利益・緊急度に基づく）
4. **CEOへの報告事項** — `PM.md` のEscalation Rulesに該当する事項、および
   Weekly Review未実施などPM運用上の懸念事項

出力形式:

```
AI SideBusiness Lab
━━━━━━━━━━━━━━
Today's Summary
新規 <n> / 開発中 <n> / 収益化 <n> / 改善中 <n>
━━━━━━━━━━━━━━
Today's Recommendation
① <案件> → <次の行き先>
② ...
━━━━━━━━━━━━━━
Priority
★★★★★ <案件>
★★★★☆ <案件>
...
━━━━━━━━━━━━━━
CEOへの報告事項
<エスカレーション事項、なければ「特になし」>
```

Portfolio Dashboardにデータがない場合は「登録済みの案件がありません。
/intake から開始してください」と案内する。

このコマンドは「会社の状況を教えて」「今どうなってる？」といった自然言語からも
同じロジックで呼び出される想定である。
