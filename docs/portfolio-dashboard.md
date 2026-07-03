# portfolio-dashboard.md — Portfolio Dashboard

すべての案件の状態を一望するための唯一の真実の源（single source of truth）。
`/intake` `/route` `/portfolio` `/review` `/status` `/search` などのコマンドは
すべてこのファイルを参照・更新する。手動での直接編集は避け、原則として
コマンド経由（PMの操作）でのみ更新する。

## 案件一覧

| ID | 案件名 | 状態 | 担当部門 | 優先度 | 利益（実績/見込み） | 最終更新日 | 備考 |
|---|---|---|---|---|---|---|---|
| PJ-001 | YouTube動画要約サービス | 評価中 | 事業評価部 | 未評価 | - | 2026-07-03 | 市場調査完了（Conditional Go提案、信頼度72%）。詳細: cases/PJ-001/research.md |

状態の凡例: 新規 / 調査中 / 評価中 / 法務確認中 / 開発中 / 運用中 / 改善中 / 撤退検討 / 撤退済

## 次に採番するID

PJ-002

## 更新履歴

| 日付 | 内容 |
|---|---|
| 2026-07-03 | PJ-001を新規登録し市場調査部へ引き渡し |
| 2026-07-03 | PJ-001: /route実行。市場調査部の成果物未提出（Exit Criteria未達）のため据え置き。Research待ち |
| 2026-07-03 | PJ-001: /research実行。cases/PJ-001/research.mdを作成しQuality Gate達成 |
| 2026-07-03 | PJ-001: /route実行。市場調査部Exit Criteria達成を確認し事業評価部へ前進 |
