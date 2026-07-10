# growth-roadmap.md — 90日ロードマップ（LIMIT LAB WORKS）

BOOTHショップ「LIMIT LAB WORKS」公開（2026-07-04）を起点とした、
最初の90日間の現実的な目標。売上そのものではなく、月5万円に到達する
ための先行指標（商品数・フォロワー数・販売実績）を段階的に積む。

## Company Phase（会社フェーズ）

以下の**Monthly Milestone**（月次の商品数・フォロワー目標）とは完全に
分離した、会社全体の成熟度を示す指標。Company Phaseの卒業は
Company Phase Gate（次項）だけで判定し、Monthly Milestoneの達成度では
判定しない。両者を混同しない。

| Phase | 内容 | 状態 |
|---|---|---|
| Phase 1 | 設計構築（会社OSの基本設計・CONSTITUTION・部門・パイプライン構築） | 完了（〜2026-07-04） |
| Phase 2 | 事業運営（実際に商品を作り、売り、改善サイクルを回す） | 進行中（2026-07-04〜） |
| Phase 3 | 未定義 | 未着手 |
| Phase 4 | 未定義 | 未着手 |
| Phase 5 | 未定義 | 未着手 |

Phase 3以降は今の時点で詳細設計しない。`docs/architecture-governance.md`
Core Rule 02「Graduation First」（将来必要になる機能を先回りして
実装しない）に従い、Phase 2卒業後に実データを踏まえて定義する。

## Company Phase Gate（Phase 2の卒業条件）

以下6条件をすべて満たした時点でPhase 2を卒業したと判断する。これが
唯一の判定基準であり、売上の多寡では判定しない。

- 商品10点以上を公開
- 改善提案30件以上を実施
- Customer Voice 100件以上を蓄積
- CEO Morning Briefを90日以上継続
- Decision Log 50件以上を記録
- 全部署が「毎日自然に動いている」状態（CEOは承認するだけで済む）

卒業後は、`docs/org-expansion-roadmap.md`のトリガー条件を推測ではなく
実データで再判定し、Phase 3の内容を初めて具体的に設計する（Premium
商品・ポートフォリオ拡大等の検討はこのタイミングで行う。詳細は
`knowledge/CEO Weekly Review/`の該当回を参照）。

## Week 1 KPI（2026-07-04〜、Monthly Milestone 1の最初のマイルストーン）

- 商品数: 3点（達成: AI Company OS Template Kit / Claude Code Prompt
  Pack / AI Business Template Pack。2026-07-04、3商品すべてBOOTHへ
  実出品完了。「商品を3点に増やす」「実出品」の両方を達成）
- X投稿: 7本（毎日1本、80:20方針。下書きは`docs/x-content-calendar-week1.md`）
- BOOTHお気に入り: 5件
- GitHubスター: 5件
- 初回販売: 1件

売上だけでなく、お気に入り・スターも初期の市場反応として扱う。

## Monthly Milestone 1（2026年7月）

- 商品3点公開
- Xフォロワー100人
- BOOTHお気に入り10件
- 初回販売1件

## Monthly Milestone 2（2026年8月）

- 商品5〜8点
- Xフォロワー300人
- 月10件販売

## Monthly Milestone 3（2026年9月）

- 商品10点以上
- 月売上3〜5万円

## 運用ルール

- 各Monthly Milestoneの達成状況はWeekly Review（`PM.md`）でCEOに報告する
- 2026-07-09以降のX投稿目標は**21本/週（1日3本・可能な限り画像付き）**
  とする（`docs/channel-strategy.md`の投稿頻度ルール。Morning Briefの
  X投稿達成率もこの目標値で算出する）
- Monthly Milestone 1の「初回販売1件」が発生した時点で、
  `docs/portfolio-strategy.md`のAnalytics部新設条件を満たし、
  Sprint 7（分析部）を開始する
- 目標未達が続く場合は、`docs/decision-framework.md`の継続/改善/撤退
  判定に従い、商品ラインナップやチャネル戦略を見直す

## Sprint方針の見直し（2026-07-04）

Analytics部を作る前に、`/morning-brief`（CEO Morning Brief）を毎日の
意思決定を支える機能として強化する方を優先する。新しい部署（Analytics・
「秘書AI」等）は増やさず、マーケティング部のCEO Morning Brief機能に
統合する。実績データ（GitHubスター・Xフォロワー・BOOTHお気に入り・
売上）はAIが自動取得できないため、`docs/daily-metrics.md`への日次報告
（人間）が前提となる。この運用が安定してから、Analytics部（販売済み
商品1件以上が条件）の検討に進む。
