# 研究単位（Research Unit）テンプレート

> ユーザー提案。「テーマ→候補→候補→候補」という単位ではなく、
> 「問い→検証→結論」という単位に一段抽象化する。研究が「現象中心」
> ではなく「問い中心」になる。すべてのRQ（Research Question）文書は
> このテンプレートの9項目**だけ**を持ち、これ以上増やさない。

## 固定された9項目

```
Research Question（研究の問い）
    ↓
Mechanism（どのメカニズムを検証するか）
    ↓
Observable（何を観測するか）
    ↓
Proxy（それを何で代理測定するか）
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

1. **Research Question**: 「HFTは速いか？」のような検証不能な問いを
   禁止する。「主体Aと主体Bの反応速度の違いは統計的に有意か」のように、
   最初から検定可能な形で立てる
2. **Mechanism**: `ALPHA_GENERATION_MAP.md`の5分類または
   `ARBITRAGE_CONSTRAINT_MAP.md`の3力のどれに対応するかを明記
3. **Observable**: 実際に観測可能なデータ（例: イベント後の累積異常
   リターン）
4. **Proxy**: Observableを測るための具体的な代理変数（例: 主体分類・
   出来高比率）。`ARBITRAGE_CONSTRAINT_MAP.md`の「測定可能な代理変数」
   要件と一致させる
5. **Hypothesis**: 支持/棄却が明確に判定できる数値命題（例:
   「中央値≥0.80」）。1つのRQ文書に複数のHypothesis（例: H_aとH_b）が
   あっても構わないが、それぞれ独立に支持/棄却を判定する
   （`RQ-001`で学んだ教訓: 「中間的な結果」という第三の判定は存在しない）
6. **Pre-registration**: イベント定義・統計モデル・フィルタ閾値を
   結果を見る前に確定する（`EVENT_EVALUATION_PIPELINE.md`①②③に対応）
7. **Test**: Permutation Test・DSR・PBO等、具体的な検定手法
8. **Evidence**: `RESEARCH_CHARTER.md`のEvidence Level（E0-E5）と
   Robustness（R0-R5）を両方記載する
9. **Negative / Positive Result**: 判定結果と、原因を断定しない解釈。
   棄却されたら`../NEGATIVE_RESULTS.md`に、却下理由を構造化タグ
   （Novelty / DSR / Mechanism / Replication / Economic rationale）
   付きで追記する

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
作成し、この9項目の見出しだけで書く。項目を追加したくなったら、まず
「本当にこの9項目のどれかに含められないか」を確認すること。
