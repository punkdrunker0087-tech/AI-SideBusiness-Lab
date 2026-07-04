# opportunity-pipeline.md — Opportunity Pipeline

「売れそう」だけでは商品化しない。CEO承認から本販売までの間に、
利用者に損をさせないための検証ステップを挟む。第四条「利用者第一」を
実際のプロセスに落とし込んだものであり、`docs/decision-framework.md`
（発掘フェーズの8軸スコアリング）と`CLAUDE.md`のフロー図（実行フェーズ）
の間をつなぐ。

## 7ステージ

```
Idea → Research → Validation → Prototype → Pilot → Production → Growth
```

| ステージ | 内容 | 担当・関連コマンド |
|---|---|---|
| Idea | 案件候補の着想（`/intake`） | PM |
| Research | 検索数・競合・需要のEvidence収集 | 市場調査部（`/research`） |
| Validation | Evidenceの品質監査、SNS反応・簡易アンケート等の裏付け | 検証部（`/validate`） |
| Prototype | 試作品（最小限の実物・サンプル）を作る | 制作部 |
| Pilot | 限定公開・少数への先行販売で実際の反応を見る | 制作部・マーケティング部 |
| Production | パイロットの結果を踏まえた本製作・本販売 | 制作部・マーケティング部 |
| Growth | 本販売後の実データに基づく分析・改善 | 分析部・改善部 |

事業評価部（`Evaluation.md`）のGo/No-Go判定・Value Score算出は
Validationの直後、Prototypeへ進む前に行う（従来通り）。

## Prototype／Pilotが必須になる条件

すべての案件に一律でPrototype/Pilotを課すと、¥480のテンプレート1点
売るだけでも過剰な手続きになる。以下のいずれかに該当する場合のみ
必須とし、該当しない場合はPM判断でスキップ理由を記録した上で
Productionへ直接進んでよい。

- 制作モードがSoftware（コードを伴う開発）を含む案件
- Asset Scoreが3以下（一度作れば終わりではなく、継続的な運用・
  サポートが必要な性質の案件）
- LIMIT LABにとって新しい商品カテゴリ（過去に前例がない種類の商品）
- 事業評価部の総合スコアが70未満（Go〜Conditional Goの境界に近い、
  不確実性が高い案件）

上記に該当しない小規模なテンプレート・Prompt・Content型の商品
（`Production.md`のContent/Templateモード中心の商品）は、Quality Gate
とValue Scoreが実質的に同等の安全装置として機能するため、Prototype/
Pilotを省略してよい。省略する場合もその判断を
`cases/<ID>/production/`または`docs/portfolio-dashboard.md`に一言
記録する。

## Pilotの具体的なやり方（該当する場合）

- 対象チャネルを1つに絞って限定公開する（例: BOOTHのみ、noteのみ）
- 価格・タイトル・サムネイルのA/Bテストと兼ねてよい
  （`Marketing.md`のA/Bテストと連動）
- 一定期間（目安1週間）または一定件数の反応を得たら、
  `knowledge/Customer Voice/`に記録し、Productionへの移行判断に使う
- Pilotの結果が悪い場合、Production前に企画を差し戻す
  （`docs/decision-framework.md`のPivot相当の扱い）
