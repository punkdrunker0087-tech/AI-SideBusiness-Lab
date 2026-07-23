# 研究単位（Research Unit）テンプレート

> ユーザー提案。「テーマ→候補→候補→候補」という単位ではなく、
> 「問い→検証→結論」という単位に一段抽象化する。研究が「現象中心」
> ではなく「問い中心」になる。すべてのRQ（Research Question）文書は
> このテンプレートの10項目**だけ**を持ち、これ以上増やさない。

> ⚠️ **改訂（ユーザー指摘への応答）**: 「研究基盤が完成したことと、
> 研究テーマの質が高いことを混同し始めている」という指摘を受け、
> 2点を修正した。①「Mechanism」を「Mechanism Candidate」に改称
> （メカニズムは検証前は仮説候補に過ぎず、確定した説明であるかの
> ように書かない）。②「Alternative Explanation」を新設し、提案した
> メカニズム以外の競合説明を明示する項目を追加した。

## 固定された10項目

```
Research Question（研究の問い、具体的で検定可能な形）
    ↓
Mechanism Candidate（検証したいメカニズムの候補。確定した説明ではない）
    ↓
Observable（何を観測するか）
    ↓
Proxy（それを何で代理測定するか、代理変数自体の妥当性の検討込み）
    ↓
Alternative Explanation（Mechanism Candidate以外にありえる競合説明）
    ↓
Hypothesis（反証可能な数値命題）
    ↓
Pre-registration（結果を見る前に固定する設計）
    ↓
Test（統計的検定手法）
    ↓
Evidence（Evidence Level・Robustness）
    ↓
Negative / Positive Result（棄却・支持の判定と解釈）
```

## 各項目の要件

1. **Research Question**: 「HFTは速いか？」「裁定主体の反応速度は？」
   のような、研究テーマの名前を問いの形に言い換えただけの粒度を
   禁止する。**RQは必ず、具体的な変数間の関係を問う形にする**
   （例: 「海外機関保有比率が高い企業ほど、決算後CARの収束は速いか」）。
   「テーマ2に着手する」ことと「RQを1本書く」ことは別の作業であり、
   テーマ名をそのままRQ欄に書いていないかを必ず確認する
2. **Mechanism Candidate**: `ALPHA_GENERATION_MAP.md`の5分類または
   `ARBITRAGE_CONSTRAINT_MAP.md`の3力のどれに対応するかを明記する。
   ただし**これは「保証されたメカニズム」ではなく「検証したい仮説的
   説明の候補」であることを常に明示する**。「裁定主体が遅い→価格が
   遅れる」という記述は、検証後にそう言えるかもしれない結論であって、
   検証前に前提として書いてはならない
3. **Observable**: 実際に観測可能なデータ（例: イベント後の累積異常
   リターン）
4. **Proxy**: Observableを測るための具体的な代理変数（例: 外国人
   保有比率・出来高比率）。`ARBITRAGE_CONSTRAINT_MAP.md`の「測定可能な
   代理変数」要件と一致させる。**Theme 2（裁定主体）・Theme 3（制約）
   では特に注意**: 「主体」も「制約」も直接観測できず、必ず代理変数
   経由になる（例: 外国人保有比率は「海外機関投資家」そのものでは
   ない、空売り比率は「裁定制約」そのものではない）。代理変数を採用
   する際は、**その代理変数が本当に測ろうとしている概念を捉えている
   かの根拠**を1文以上書く。根拠が書けない代理変数は使わない
5. **Alternative Explanation**: Mechanism Candidateが正しくなくても
   同じ観測結果を説明できる、競合する説明を最低2つ挙げる（例:
   「価格反応が遅い」に対して、流動性・銘柄サイズ・ボラティリティ・
   開示の複雑さ・アナリストカバレッジ数、等）。Hypothesisの検定
   結果が支持された場合でも、Alternative Explanationを積極的に
   棄却できていない限り、Mechanism Candidateが正しいと断定しない
6. **Hypothesis**: 支持/棄却が明確に判定できる数値命題（例:
   「中央値≥0.80」）。1つのRQ文書に複数のHypothesis（例: H_aとH_b）が
   あっても構わないが、それぞれ独立に支持/棄却を判定する
   （`RQ-001`で学んだ教訓: 「中間的な結果」という第三の判定は存在しない）
7. **Pre-registration**: イベント定義・統計モデル・フィルタ閾値を
   結果を見る前に確定する（`EVENT_EVALUATION_PIPELINE.md`①②③に対応）
8. **Test**: Permutation Test・DSR・PBO等、具体的な検定手法。
   **Mechanism Candidateが因果関係を主張する場合**（例: 「主体Xの
   保有比率が原因でCARの収束が速い」）、相関だけでなく、考えられる
   交絡要因（Alternative Explanationで挙げたもの）を明示的にDAG
   （因果グラフ）で1枚描き、どの変数を統制する必要があるかを検討する。
   相関の確認だけで因果を主張しない
9. **Evidence**: `RESEARCH_CHARTER.md`のEvidence Level（E0-E5）と
   Robustness（R0-R5）を両方記載する
10. **Negative / Positive Result**: 判定結果と、原因を断定しない解釈。
    棄却されたら`../NEGATIVE_RESULTS.md`に、却下理由を構造化タグ
    （Novelty / DSR / Mechanism / Replication / Economic rationale）
    付きで追記する。支持された場合も、Alternative Explanationを
    排除できていなければ「Mechanism Candidateが正しい」ではなく
    「Mechanism Candidateと矛盾しない」という弱い表現に留める

## レビュー運用（新しいマップ・憲章を増やす代わりに、ユーザー提案）

新しいメタドキュメントを増やす代わりに、**各Research Unitについて
以下の5点を満たしているかをレビューする運用**に切り替える:

1. Mechanism（確定した説明）とMechanism Candidate（検証前の仮説）を
   混同していないか
2. RQがテーマ名の言い換えではなく、具体的で検定可能な粒度になって
   いるか
3. 使用した代理変数の妥当性が、根拠つきで検討されているか
4. Alternative Explanation（競合する説明）が明示されているか
5. 因果関係を主張する場合、DAGなど因果構造の検討を経ているか

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
作成し、この10項目の見出しだけで書く。項目を追加したくなったら、
まず「本当にこの10項目のどれかに含められないか」を確認すること。
