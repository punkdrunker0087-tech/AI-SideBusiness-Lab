# PRINCIPLES.md — 運営原則（EXP-011）

制定: 2026-07-24（CEO指示）／改定: 2026-07-24（昇格条件を厳格化、状態管理を追加）

## 知識昇格モデル

```
Experiment（一回限りの検証）
  ↓
Review（週次のResearch Review）
  ↓
Lesson（何度か使えそうな知見）
  ↓
Principle（何度検証しても覆らない運営原則）
```

| ファイル | 段階 |
|---|---|
| `EXPERIMENTS.md` | Experiment |
| `WEEKLY.md`のResearch Review | Review |
| `LESSONS.md` | Lesson |
| 本ファイル | Principle |

## Principle昇格条件（改訂版・2026-07-24）

1. **Accepted Lessonであること**
2. **3件以上の独立した文脈で再確認されていること。** 「文脈」とは
   例えばドキュメント設計・Routine運用・実験管理のように**性質の異なる
   領域**を指す。同じ原因を3回繰り返しただけ、実質的に同じ実験を3回
   行っただけでは満たさない（機械的なカウントを避けるための明文化）
3. **反例が見つかっていないこと**
4. **CEO承認**

```
Candidate Lesson
  ↓
Accepted Lesson
  ↓
3件以上の独立した文脈で再確認 + 反例なし
  ↓
Principle候補
  ↓
CEO承認
  ↓
PRINCIPLE-00X
```

**Principleは簡単には増えない設計にする。**

## Principleの状態

`LESSONS.md`と同様、Principleにも状態を持たせる。「原則だったが後に
撤回された」という履歴も残せるようにする。

| 状態 | 意味 |
|---|---|
| Candidate Principle | 3文脈確認済みだがCEO未承認 |
| Accepted Principle | CEO承認済みの正式な運営原則 |
| Deprecated Principle | もう有効でないと判断されたが履歴は残す |
| Superseded Principle | より良いPrincipleに置き換えられた |

## 現状（2026-07-24時点）

まだ改訂後の条件（3件の**独立した文脈**＋反例なし）を満たした
`Accepted` Lessonはない。**最有力候補は Single Source of Truth**
（`LESSON-002`「運用手順は仕様書参照型にすると保守性が高い」／
`LESSON-004`「SSOTを導入しても実装が原則を満たすかは別途レビューが
必要」に由来）。

文脈を分けて確認すると:
- **Routine運用**: 確認済み（EXP-009・`ROUTINE.md`によるトリガーの
  仕様書参照化）
- **ドキュメント設計**: 確認済み（EXP-009・`ROUTINE.md`と`WEEKLY.md`の
  Research Review重複を発見・解消）
- **実験管理**: 未確認

上記2件は厳密には同一の実験（EXP-009）から派生した観測であり、
**独立した3文脈という条件はまだ満たさない。** 安易な繰り上げを避け、
Lesson段階のまま観察を続ける（憲法第4条: 検証していないことを
断言しない）。

## Principle一覧

（まだ登録なし。改訂後の条件を満たすLessonが出た時点で、
CEO承認を経て`PRINCIPLE-001`から採番する）
