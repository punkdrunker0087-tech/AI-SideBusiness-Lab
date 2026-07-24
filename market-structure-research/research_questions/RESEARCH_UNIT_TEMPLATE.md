# 研究単位（Research Unit）テンプレート

> ユーザー提案。「テーマ→候補→候補→候補」という単位ではなく、
> 「問い→検証→結論」という単位に一段抽象化する。

> ⚠️ **改訂（最終版、ユーザー指摘への応答）**: テンプレートが
> Mechanism Candidate・Alternative Explanation・DAG要件の追加で
> 段々重くなり、「RQを書くのに2時間かかる」状態に近づいていた。
> **研究単位は軽くあるべき**という指摘を受け、必須項目と条件付き
> 必須項目を分離した。**テンプレートの拡張はこれを最後にする。**
> 以降は同じテンプレートで10〜20本のResearch Unitを運用し、
> 「どの項目が実際に使われ、どの項目が使われなかったか」を観察して
> から次の改訂を検討する（`RESEARCH_CHARTER.md`参照）。

## 必須項目（すべてのRQが持つ）

```
Research Question（具体的で検定可能な問い）
    ↓
Observable（何を観測するか）
    ↓
Hypothesis（反証可能な数値命題）
    ↓
Pre-registration（結果を見る前に固定する設計）
    ↓
Test（統計的検定手法）
    ↓
Evidence（Evidence Level・Robustness）
    ↓
Decision（採択・棄却・保留・再実験・データ不足）
```

⚠️ ユーザー提案の必須リストは「RQ・Observable・Hypothesis・Test・
Evidence」の5つだったが、**Pre-registrationは必須から外さない**。
理由: Pre-registrationがなければ、Test・Evidenceで何を計算しても
後付けの言い訳が可能になり、これまで繰り返し警戒してきた
p-hacking・符号フィッシングの歯止めが失われる。これは唯一、ユーザー
提案からの意図的な逸脱であり、理由を明記した上でそのままにする。

## 条件付き必須項目（該当する場合のみ）

| 項目 | いつ必須になるか |
|---|---|
| **Mechanism Candidate** | 「なぜそうなるか」の仮説的説明を提示する場合 |
| **Proxy** | Observableを直接観測できず、代理変数を使う場合（Theme 2・3ではほぼ常に該当） |
| **Alternative Explanation** | Mechanism Candidateを書く場合（Mechanism Candidateを主張するなら必ずセットで書く） |
| **DAG + Blocking Strategy** | 因果関係を主張する場合（相関の報告だけなら不要） |

### 条件付き項目の中身

- **Mechanism Candidate**: `ALPHA_GENERATION_MAP.md`の5分類または
  `ARBITRAGE_CONSTRAINT_MAP.md`の3力のどれに対応するかを明記する。
  これは検証前の**仮説的説明の候補**であり、確定した説明として
  書かない
- **Proxy**: 代理変数を採用する根拠を1文以上書く。根拠が書けない
  代理変数は使わない
- **Alternative Explanation**: Mechanism Candidate以外の競合説明を
  最低2つ挙げ、それぞれに**優先順位**（最もありそう/ありそう/可能性
  低い）と**反証コスト**（既存データで統制可能か、追加データが必要か、
  取得困難か、を★の数等で簡潔に）を記載する。これにより次に何を
  検証すべきかの優先順位が自然に決まる
- **DAG + Blocking Strategy**: 因果グラフを描いたら、それだけで
  終わらせず、**どの交絡経路をどう統制して検証するか**（例:
  「大型株のみで検証」「カバレッジ数で層別」）まで必ずセットで書く。
  DAGは描くものではなく、検証計画に落とすもの

## Decisionの選択肢

Evidence（統計的な支持/棄却の水準）とDecision（この知見をどう
扱うか）は別物である。EvidenceがE2でもDecisionは「保留」かもしれない。

- **棄却**: Mechanism Candidateまたは主仮説を明確に棄却し、これ以上
  追わない
- **保留**: 棄却も採択もできない、追加データ・追加検証が必要
- **昇格**: Evidence Level・Robustness基準（`RESEARCH_CHARTER.md`の
  E3-R2以上）を満たし、投資候補として扱ってよい
- **再実験**: 設計上の懸念（Alternative Explanation未統制等）があり、
  設計を改めて再検証する
- **データ不足**: 現在保有するデータでは検証が完了できない

半年後に「これ何だったっけ」を防ぐため、Decisionは必ず1つ選ぶ。

## レビュー運用（変更なし）

新しいメタドキュメントを増やす代わりに、各Research Unitについて
以下を満たしているかをレビューする:

1. Mechanism（確定した説明）とMechanism Candidate（検証前の仮説）を
   混同していないか
2. RQがテーマ名の言い換えではなく、具体的で検定可能な粒度になって
   いるか
3. 代理変数を使う場合、その妥当性が根拠つきで検討されているか
4. Mechanism Candidateを書く場合、Alternative Explanationが
   優先順位・反証コストつきで明示されているか
5. 因果関係を主張する場合、DAG＋Blocking Strategyまで書かれているか
6. Decisionが明記されているか

## ディレクトリ構成

```
research_questions/
  RESEARCH_UNIT_TEMPLATE.md   ← このファイル
  theme1_price_reaction_speed/
    RQ-001_xxx.md
    RQ-002_xxx.md ...
  theme2_arbitrage_agents/
    RQ-0xx_xxx.md ...
  theme3_arbitrage_constraints/
    RQ-0xx_xxx.md ...
  pipeline_validation/
    PV-001_xxx.md ...  ← ネガティブコントロール等、市場構造の問いでは
                          なくパイプライン自体の検証（RQ番号を割り当てない）
```

新しいRQを始める際は、該当テーマのフォルダに`RQ-NNN_短い説明.md`を
作成し、必須7項目＋該当する条件付き項目だけで書く。
