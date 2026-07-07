# portfolio-dashboard.md — Portfolio Dashboard

すべての案件の状態を一望するための唯一の真実の源（single source of truth）。
`/intake` `/route` `/portfolio` `/review` `/status` `/search` などのコマンドは
すべてこのファイルを参照・更新する。手動での直接編集は避け、原則として
コマンド経由（PMの操作）でのみ更新する。同時進行数の上限・判定ごとの
運用アクションは `docs/portfolio-strategy.md` に従う。

## アクティブ案件数

3 / 3（上限）

## 案件一覧

| ID | 案件名 | 状態 | 担当部門 | 優先度 | 利益（実績/見込み） | 最終更新日 | 備考 |
|---|---|---|---|---|---|---|---|
| PJ-001 | YouTube動画要約サービス | Backlog（保留） | PM | 保留（PJ-004着手のためアクティブ枠を明け渡し） | - | 2026-07-08 | CEO承認: 日本語ビジネス/研修動画特化への絞り込みが前提。Software制作が必要なためマーケティング部実装まで保留。2026-07-08、PJ-004（株式投資研究）の即時着手のためBacklogへ降格 |
| PJ-002 | AI Business Template Factory（LIMIT LAB WORKS） | 公開済み（初回販売待ち） | CEO（人間） | 最優先（総合79点/Go、Asset Score★5） | - | 2026-07-06 | BOOTH: https://limit-lab.booth.pm/ 。X: https://x.com/LimitLabJP （フォロワー80名、07-07時点。詳細は`docs/daily-metrics.md`）。商品ライン: ①AI Company OS Template Kit（¥980）②Claude Code Prompt Pack（¥480）③AI Business Template Pack（¥480）④Research Department Prompt（¥980, Value Score81）。4商品すべてBOOTH公開済み。商品数4/10（Phase2卒業条件）。7/6 19:30時点、初回売上まだ0件。初回売上が出次第Sprint 7（分析部）を開始 |
| PJ-003 | VRChat向けAI活用テンプレート・ワークフロー商品 | 検証中 | 検証部 | 次点（PJ-002より下位、急がない） | - | 2026-07-06 | ユーザー提案。市場調査完了（`cases/PJ-003/research.md`、Confidence 75%、Recommendation: Conditional Go）。市場規模（BOOTH3Dモデルカテゴリ104億円）は裏付けあるが、無料競合（UnityMCP-VRC等）とLIMIT LABの専門実績不足がリスク。CEO判断によりショップ分割・サブブランド化は行わず、LIMIT LAB WORKS（PJ-002）を最優先で推進（詳細は`knowledge/Decision Log/2026-07-06-pj003-priority-and-shop-split-deferred.md`） |
| PJ-004 | 株式投資研究（自社内部運用・非提供） | CEO判断待ち | CEO | 要CEO判断（事業評価部案: Pivot、42点） | - | 2026-07-08 | 事業評価部が独立採点し総合42点でPivot案（`cases/PJ-004/score-history.md`）。市場性15・収益性20が自社内部運用のため構造的に低い。開発容易性90・AI自動化率70は高評価。Value Score63。投資額上限¥100,000・最終発注は必ずCEO・PJ-002を圧迫しない時間配分の3条件は承認済み |
| PJ-005 | 電脳せどり自動化・無在庫販売の越境EC | Backlog（新規） | 未着手 | 保留（Backlog登録のみ） | - | 2026-07-08 | ユーザー提案。自社内部で運用する実ビジネス（商品として他者へ提供するものではない）。仕入れ・決済・マーケットプレイスAPI連携等、実資金とSoftware実装が必要。着手判断は今後改めて行う |

状態の凡例: 新規 / 調査中 / 検証中 / 評価中 / CEO判断待ち / 開発待ち / 法務確認中 / 制作中 / 制作完了 / マーケティング準備中 / 公開済み（初回販売待ち） / 運用中 / 改善中 / 撤退検討 / 撤退済

## 次に採番するID

PJ-006

## 更新履歴

| 日付 | 内容 |
|---|---|
| 2026-07-03 | PJ-001を新規登録し市場調査部へ引き渡し |
| 2026-07-03 | PJ-001: /route実行。市場調査部の成果物未提出（Exit Criteria未達）のため据え置き。Research待ち |
| 2026-07-03 | PJ-001: /research実行。cases/PJ-001/research.mdを作成しQuality Gate達成 |
| 2026-07-03 | PJ-001: /route実行。市場調査部Exit Criteria達成を確認し事業評価部へ前進 |
| 2026-07-03 | 検証部・事業評価部を新設。フローをResearch→Validation→Evaluationに変更したため、PJ-001を検証部の監査対象として据え置き直す |
| 2026-07-03 | PJ-001: /validate実行。チェックリスト11項目すべて達成しPASS。事業評価部へ前進 |
| 2026-07-03 | PJ-001: /evaluate実行。総合64点でConditional Go判定案を作成しCEOへ提出 |
| 2026-07-03 | PJ-001: CEO判断。条件付き投資を承認（ニッチ特化が前提）。開発部未実装のため開発待ちとし、PMはPJ-002の投入を優先する |
| 2026-07-03 | PJ-002を新規登録し市場調査部へ引き渡し。B2B・ニッチ・低競争タイプの案件としてPJ-001と並行運用を開始 |
| 2026-07-03 | PJ-002: /research実行。cases/PJ-002/research.mdを作成しQuality Gate達成。Recommendation: Go（信頼度80%） |
| 2026-07-03 | PJ-002: /validate実行。チェックリスト11項目すべて達成しPASS。事業評価部へ前進 |
| 2026-07-03 | PJ-002: /evaluate実行。総合79点でGo判定案、Asset Score★5（積極投資）を作成しCEOへ提出 |
| 2026-07-03 | PJ-002: CEO判断。Go・積極投資を承認。開発部/マーケティング部未実装のため実行は保留だが、PJ-001より優先順位を上位に変更 |
| 2026-07-03 | PJ-002: 法務チェック実施。法的リスクなし（許容範囲内）。ライセンス・AI開示・特定商取引法表記に関する修正指示を制作部へ |
| 2026-07-03 | PJ-002: /produce実行。Packageモードで「AI Company OS Template Kit v1」を制作。Quality Gate全項目達成（PMレビュー含む）。マーケティング部へ引き渡し（マーケティング部未実装のため出品自体は保留） |
| 2026-07-03 | PJ-002: /marketing実行。BOOTH/note向け6点セット（販売ページ・X投稿3本・note記事・商品説明・SEOタイトル・サムネイル指示書）を作成。価格決定（¥1,480/¥1,980）。Exit Criteria達成し分析部へ引き渡し（分析部未実装のため実際の出品・売上計測は次Sprintの課題） |
| 2026-07-03 | Sprint 6.5開始。「No Internal Completion」ルールをportfolio-strategy.mdへ追加。CEO判断により価格を¥980へ改定 |
| 2026-07-03 | PJ-002: 配布用ZIP（ai-company-os-template-kit-v1.zip、37ファイル）を実際に作成しユーザーへ送付。BOOTHへの実出品操作はCEO（人間）が行うため、状態は「公開待ち」のまま。架空の公開日・売上は記録しない |
| 2026-07-04 | CEO（人間）がBOOTHショップ「LIMIT LAB WORKS」を実際に開設・公開（https://limit-lab.booth.pm/）。X（https://x.com/LimitLabJP）も公開。ブランド情報をdocs/brand.mdに記録。初回売上はまだ発生していないため、Analytics部の新設条件は未達のまま |
| 2026-07-04 | CEO方針転換。「AI Company OSを売る」から「LIMIT LABブランドを育てる」へ。docs/product-line.mdでStarter/Standard/Premiumの商品ライン戦略を策定 |
| 2026-07-04 | PJ-002: 2つ目の商品「Claude Code Prompt Pack」（Starter, ¥480）を法務チェック→/produce→/marketingで制作。19ファイルのZIPを作成しユーザーへ送付。BOOTH出品は人間の操作待ち |
| 2026-07-04 | CEO（人間）がGitHubリポジトリを公開。README冒頭にBOOTH/Xリンクを追加 |
| 2026-07-04 | PJ-002: 3つ目の商品「AI Business Template Pack」（Starter, ¥480、議事録/SOP/マニュアル/要件定義/レビューシートの5テンプレート）を法務チェック→/produce→/marketingで制作。9ファイルのZIPを作成しユーザーへ送付。商品数3/3（Week1目標達成）。BOOTH出品は人間の操作待ち |
| 2026-07-04 | CEO（人間）が3商品すべて（AI Company OS Template Kit / Claude Code Prompt Pack / AI Business Template Pack）をBOOTHへ実際に公開。Week1「商品を3点に増やす」「実出品」が完了。初回売上・お気に入り数はまだ未報告 |
| 2026-07-05 | PJ-002: 4つ目の商品「Research Department Prompt」（Standard下限, ¥980、市場調査/品質監査/8軸スコアリングの3プロンプト）を法務チェック→/produce→/marketingで制作。Value Score81/100で基準達成。7ファイルのZIPを作成しユーザーへ送付。BOOTH出品は人間の操作待ち |
| 2026-07-05 | CEO（人間）が4つ目の商品「Research Department Prompt」をBOOTHへ実際に公開。4商品すべて公開済みとなる |
| 2026-07-06 | CEO（人間）がnote記事2稿目（`cases/PJ-002/marketing-note-002-architecture-governance.md`「AI会社に『これ以上増えるな』というルールを持たせた話」）を実際にnoteへ公開 |
| 2026-07-06 | PJ-003を新規登録し市場調査部へ引き渡し（VRChat向けAI活用テンプレート・ワークフロー商品、ユーザー提案） |
| 2026-07-08 | CEO（人間）がnote記事3稿目（`cases/PJ-002/marketing-note-003-vrchat-conditional-go.md`「儲かりそうな新市場の話が来たので、AIに調べさせてから『今はやらない』と決めた話」）を実際にnoteへ公開。7/8時点でnote3本の実績（ビュー20/17/12、スキ計1、コメント0）を確認 |
| 2026-07-08 | CEOがBOOTHショップ・商品ともに公開設定であることを確認。7/7のWebFetchが「非公開」と表示したのはツール側（ボット判定）の誤検知と判明。「非公開設定が原因で売上が出ていない」という仮説は解消。売上0の原因は別（集客・転換率・価格・認知等）にあると再整理 |
| 2026-07-06 | PJ-003: /research実行。cases/PJ-003/research.mdを作成しQuality Gate達成（検証部レビュー除く）。Confidence 75%、Recommendation: Conditional Go。検証部へ引き渡し |
| 2026-07-08 | CEOより新規案件2件の提案（株式投資研究、電脳せどり自動化・無在庫越境EC）。いずれも商品提供ではなく自社内部運用。PJ-004（株式投資研究）はCEO指示により即時着手、PJ-005（電脳せどり）はBacklog登録のみ |
| 2026-07-08 | アクティブ枠（3/3）超過のため、PJ-001（次点・7/3以降動きなし）をBacklogへ降格しPJ-004の着手枠を確保（CEO承認）。PJ-004を新規登録し市場調査部へ引き渡し。PJ-005も新規登録しBacklogで保持 |
| 2026-07-08 | PJ-004: /research実行。cases/PJ-004/research.mdを作成しQuality Gate達成（検証部レビュー除く）。Confidence 70%、Recommendation: Conditional Go（自己資金の範囲内であること等を条件）。検証部へ引き渡し |
| 2026-07-08 | PJ-004: CEOが投資額上限を¥100,000に決定。Conditional Goの条件のうち「投資額上限の事前設定」を充足 |
| 2026-07-08 | PJ-004: CEOが残る2条件（最終発注は必ずCEO／PJ-002運営を圧迫しない時間配分）を承認。あわせて「実投資より先に情報収集・投資判断の有効性検証を優先する」方針を明示 |
| 2026-07-08 | PJ-004: /validate実行。初回はEvidence 3・4が同一URL（news.mynavi.jp記事）の重複でREWORK。市場調査部がEvidence統合により修正し、再検証でPASS。事業評価部へ前進 |
| 2026-07-08 | PJ-004: /evaluate実行。8軸独立採点で総合42点、Pivot案（市場調査部のConditional Goより厳しい判定）。自社内部運用のため市場性・収益性が構造的に低いことが主因。Value Score63。CEOへ判断を提出 |
