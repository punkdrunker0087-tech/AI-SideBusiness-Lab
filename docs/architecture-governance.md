# architecture-governance.md — LIMIT LAB Architecture Governance v1.0

## Purpose

LIMIT LABは「機能を増やすこと」を目的としない。目的は、持続可能な
事業を構築することである。そのため、システムは常に必要最小限
（Minimum Viable Operating System）を維持する。

この文書は`CONSTITUTION.md`「新機能・新部署・新エージェント追加の
ルール」（Purpose/Mission/Vision/Values/Constitutionのどれに貢献するか
を明確にする）を補完する、**運用面のゲート**である。CONSTITUTION.mdが
「なぜやるか」を問うのに対し、本文書は「今やるべきか、他で代替
できないか」を問う。

---

## Core Rule 01: Minimum Viable Operating System（MVOS）

LIMIT LABは「最小構成で最大成果を出す」ことを最優先とする。新しい
Module・Agent・Workflow・Automationは、卒業ゲート達成に直接貢献しない
限り実装してはならない。

## Core Rule 02: Graduation First

すべての開発は、現在のPhaseの卒業条件（Graduation Gate）達成を目的と
する。将来必要になる機能を先回りして実装してはならない。必要になった
時点で追加する。

現在のPhase 2卒業条件は`docs/growth-roadmap.md`の通り（商品10点以上・
改善30件以上・Customer Voice 100件以上・Morning Brief 90日以上継続・
Decision Log 50件以上・全部署が自然に動いている状態）。

## Core Rule 03: Architecture Change Gate（ACG）

Architecture変更（新しいModule・Agent・部署・ドキュメント・定期儀式の
追加）時は、必ず以下の8ステップを順に評価する。途中でNOが出た時点で
その手前の代替案を採用する。

| Step | 問い | NOの場合 |
|---|---|---|
| 1 | この機能は現在のPhaseに必要か？ | 却下 |
| 2 | 卒業ゲートへ直接貢献するか？ | 却下 |
| 3 | 既存Moduleへ統合できないか？ | 統合可能なら新Module禁止 |
| 4 | 既存SOPで運用できないか？ | 可能ならSOP更新のみ |
| 5 | 運用時間は増えないか？（目安30分以内） | 超えるなら却下 |
| 6 | Knowledge Baseへ保存できるか？ | できないなら却下 |
| 7 | 改善ループへ接続できるか？ | できないなら却下 |
| 8 | 半年後も必要と言えるか？ | 一時的用途なら却下 |

## Core Rule 04: One Purpose Principle

1つのModuleは1つの責任だけ持つ。複数責任は禁止。

## Core Rule 05: Reuse First

新規作成より再利用を優先する。優先順位は以下の通り。最後の手段として
のみ新Moduleを検討する。

```
Knowledge → SOP → Prompt → Workflow → Automation → New Module
```

## Core Rule 06: Automation is Expansion

自動化はPhaseが進むごとに追加する。Phase 2では必要最低限のみとする。

## Core Rule 07: Feature Freeze

卒業ゲート未達成中は、新機能開発を凍結できる。優先順位は
「卒業ゲート ＞ 機能追加」。

## Core Rule 08: Module Retirement

不要Moduleは禁止。使われないModule・Agentは削除する。

## Core Rule 09: Weekly Architecture Review

新しい儀式は作らない（Reuse First原則）。既存の
`knowledge/CEO Weekly Review/`（PM.md「CEO定例レビュー」）に、以下の
評価項目を追加する形で運用する。

- 増えたModule・SOP・Prompt数
- 運用時間の増減
- 保守性（1人で回せているか）
- 卒業ゲート進捗

増えすぎている場合は、その回のレビューで削減案を提案する。

## Core Rule 10: Build Less, Learn More

LIMIT LABは機能を作る組織ではない。学習する組織である。毎週増えるべき
ものはModuleではなく、Knowledgeである（`knowledge/`配下の蓄積）。

---

## Claude Codeの必須判断フロー

Claude Codeは新しい実装（Module・Agent・部署・ドキュメント・定期儀式）
を提案・実装する前に、必ず以下を実施する。

```
① この提案は現在のPhaseに必要か？
↓
② 卒業ゲートへ直結するか？
↓
③ 既存Moduleへ統合可能か？
↓
④ SOP追加で代替可能か？
↓
⑤ Prompt追加で代替可能か？
↓
⑥ Workflow追加で代替可能か？
↓
⑦ 自動化追加で代替可能か？
↓
⑧ 本当に新Moduleが必要か？
↓
YESの場合のみ実装許可
```

---

## LIMIT LAB Development Constitution（最上位ルール）

- LIMIT LABは「最も多くの機能を持つAIシステム」を目指さない
- LIMIT LABは「最も少ない構成で、最も高い成果を継続的に生み出せる
  事業OS」を目指す
- すべての設計判断は、この原則を基準に行う
- 卒業ゲートに貢献しない機能は実装しない
- 既存資産で解決できる問題のために、新しい複雑さを持ち込まない
- 仕組みは必要になったときにだけ追加し、一度作った知識・SOP・
  ワークフローは最大限再利用する
- LIMIT LABの成長とは、機能数の増加ではなく、「知識資産・仕組み資産・
  事業資産」が積み重なり、より少ない労力でより大きな成果を生み出せる
  ようになることである
