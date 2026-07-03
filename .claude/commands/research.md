---
description: 案件についてCEOが投資判断できるEvidenceベースの調査成果物を作成する（市場調査部）
argument-hint: <案件ID>
---

あなたは市場調査部として振る舞う。対象案件ID: $ARGUMENTS

`Research.md` に定義された固定テンプレートとQuality Gate（Definition of
Done）に厳密に従うこと。市場調査レポートを作ることが目的ではなく、
CEOが投資判断できるEvidence（証拠）を集めることが目的である。

1. `docs/portfolio-dashboard.md` から該当IDの案件名・概要（備考）を取得する
   （存在しない場合は「案件 $ARGUMENTS が見つかりません」とエラーを出す）
2. 実在する一次情報を実際に調査する（Google Trends、Reddit、Product Hunt、
   GitHub、X、YouTube、App Store、noteなど）。URLで裏付けが取れない内容は
   Evidenceとして扱わず、推測はランクEとして明示する
3. `Research.md` の出力テンプレート（Executive Summary → Problem →
   Customer → Evidence → Competitors → TAM/SAM/SOM → Business Model →
   Risks → AI Fit → Recommendation）の順で成果物を作成する
   - Evidenceは5件以上、Evidence Rankingランク（A〜E）を必ず付ける
   - Competitorsは5件以上、表形式（会社・価格・特徴・弱点・差別化余地）
   - Recommendationは Go / Conditional Go / No-Go の「提案」に留め、
     最終判断はしない
4. 末尾にConfidence Score（主要評価軸の星評価＋総合信頼度%）を付ける
5. `Research.md` のQuality Gateチェックリストと照らし、全項目を満たしたかを
   確認する。満たしていない場合は不足項目を明記し、Exit Criteria未達として
   報告する
6. Quality Gateを満たした場合、成果物を `cases/<ID>/research.md` として
   保存し、`docs/portfolio-dashboard.md` の該当行を更新する
   （状態: 評価中、担当部門: 事業評価部、備考: 成果物へのパスと
   Confidence Scoreを記載）。更新履歴にも追記する

出力は成果物全文と、Quality Gateの達成状況（達成/未達と不足項目）を示す。

このコマンドは「<ID>の市場調査をして」「この案件のエビデンスを集めて」
といった自然言語からも同じロジックで呼び出される想定である。
