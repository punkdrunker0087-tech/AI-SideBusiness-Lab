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
追加）時は、必ずWhy → When → Howの順に評価する。途中でNOが出た時点で
その手前の代替案を採用する。

### Why（CONSTITUTIONとの整合性）

`CONSTITUTION.md`「新機能・新部署・新エージェント追加のルール」に従い、
Purpose・Mission・Vision・Valuesのどれに貢献するかを1行で明確にする。
説明できない場合は却下。

### When（Company Phaseとの整合性）

| Step | 問い | NOの場合 |
|---|---|---|
| 1 | 現在のCompany Phaseに必要か？（`docs/growth-roadmap.md`） | 却下 |
| 2 | Company Phase Gate（卒業ゲート）へ直接貢献するか？ | 却下 |

### How（Reuse Firstの実践）

| Step | 問い | NOの場合 |
|---|---|---|
| 3 | 既存Moduleへ統合できないか？ | 統合可能なら新Module禁止 |
| 4 | 既存SOPで運用できないか？ | 可能ならSOP更新のみ |
| 5 | 既存Promptで代替できないか？ | 可能ならPrompt追加のみ |
| 6 | 既存Workflowで代替できないか？ | 可能ならWorkflow更新のみ |
| 7 | 既存Automationで代替できないか？ | 可能ならAutomation更新のみ |
| 8 | 運用時間は増えないか？（目安30分以内） | 超えるなら却下 |
| 9 | Knowledge Baseへ保存できるか？ | できないなら却下 |
| 10 | 改善ループへ接続できるか？ | できないなら却下 |
| 11 | 半年後も必要と言えるか？ | 一時的用途なら却下 |

Why→Whenを通過したものだけがHowの検討に進む。Howで代替できないと
判明した場合のみ、新しいModule・Agent・部署の追加を許可する。

## Core Rule 03.5: Business Impact Gate

Architecture Change Gateを通過した提案は、最後にBusiness Impactを
評価する。評価対象は「この変更は現在のCompany Phaseの卒業へどれだけ
寄与するか」。

| 分類 | 基準 |
|---|---|
| Critical | 卒業ゲートの複数項目に直接寄与する |
| High | 卒業ゲートの1項目に直接寄与する |
| Medium | 卒業ゲートへの寄与は間接的だが明確 |
| Low | 寄与はごくわずか |
| None | 卒業ゲートへの寄与を説明できない |

**Noneに分類された場合、実装を禁止する。**

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

## Core Rule 11: No Silent Expansion

機能・Module・SOP・Prompt・Workflow・Automation・Agentの追加は、必ず
明確な理由を持つこと。以下を理由にした追加は禁止する。

- 便利そう
- AIなら簡単
- 将来使うかもしれない
- 面白そう

追加は、Company Phase Gate（卒業）またはPurpose・Mission・Vision・
Valuesへ直接貢献する場合のみ許可する。

## Core Rule 12: Documentation Synchronization

以下の文書群は整合性を維持する。同一内容を複数箇所に重複して書かない。
一方を変更した場合、他方は参照関係（リンク・一行要約）のみ更新する。

- `CONSTITUTION.md`
- `docs/growth-roadmap.md`（Company Phase / Company Phase Gate）
- `PM.md`（CEO定例レビュー）
- `knowledge/CEO Weekly Review/`
- `docs/architecture-governance.md`（本文書）

新しいドキュメントを追加した場合も、内容を重複させず`LIMIT-OS.md`に
一行だけ追記する（`CONSTITUTION.md`の新機能追加ルールと同じ考え方）。

---

## Development Decision Flow（開発判断フロー）

Claude Codeは新しい実装（Module・Agent・部署・ドキュメント・定期儀式）
を提案する前に、必ず以下の順序で判断する。途中で条件を満たさない場合、
実装してはならない。

```
Idea
↓
Purpose・Mission・Vision・Values（CONSTITUTION.md、Why）
↓
Company Phase（現在のPhaseに必要か）
↓
Graduation Gate（卒業ゲートへ直結するか）
↓
Architecture Change Gate（既存Moduleで代替できないか、How）
↓
Business Impact Gate（Critical/High/Medium/Low/None。Noneなら却下）
↓
Reuse First（Knowledge→SOP→Prompt→Workflow→Automation→New Module）
↓
Implementation（実装。ここまで到達した場合のみ）
↓
Knowledge Base（`knowledge/`への記録）
↓
CEO Weekly Review（次回のレビューで報告）
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
