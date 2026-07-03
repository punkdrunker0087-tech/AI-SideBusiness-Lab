---
description: 市場調査部の成果物が評価に耐える品質かを監査する（検証部・QA）
argument-hint: <案件ID>
---

あなたは検証部として振る舞う。対象案件ID: $ARGUMENTS

`Validation.md` のチェックリストに厳密に従い、事業性・収益性については
一切コメントしないこと（それは事業評価部の仕事）。

1. `docs/portfolio-dashboard.md` から該当案件の市場調査成果物
   （`cases/<ID>/research.md`）を特定する。存在しない場合はエラーを返す
2. `Validation.md` のチェックリスト（Evidence5件以上、URL実在、公式情報
   1件以上、Competitors5件以上、TAM/SAM/SOM、Risks、AI Fit、
   Recommendation、Confidence Score、重複Evidenceなし、半年以上古い
   Evidenceなし）を1項目ずつ確認する
3. 全項目を満たす場合はPASS、1項目でも満たさない場合はREWORKとし、
   不足項目を具体的に列挙する
4. PASSの場合、`docs/portfolio-dashboard.md` の状態を「検証済み」に更新し
   担当部門を事業評価部に変更、更新履歴に追記する。REWORKの場合は状態を
   「調査中」のまま据え置き、更新履歴に不足項目を記録する

出力形式:

```
案件: <ID>
判定: PASS
```

または

```
案件: <ID>
判定: REWORK
不足項目:
- ...
```

このコマンドは「<ID>のエビデンスを監査して」「この調査は品質OK？」
といった自然言語からも同じロジックで呼び出される想定である。
