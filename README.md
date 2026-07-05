# AI-SideBusiness-Lab

> ⭐ **AI Company OS Template Kit** — 「ひとり社長のためのAI経営OS」
> （An AI Executive Operating System for Solopreneurs）— LIMIT LAB WORKS発
> 🛒 **BOOTHはこちら**: https://limit-lab.booth.pm/
> 🐦 **Xはこちら**: https://x.com/LimitLabJP

Claude Code上でCEO・PM・7部門をAIエージェントとして動かし、副業アイデアの
調査・検証・評価・制作・販売・改善までを半自動で回す「AI会社OS」。

**この会社OSがやっているのは「会社を運営すること」ではなく、「社長の
経営判断を毎朝支援すること」です。** 情報収集・KPI整理・リスク整理・
優先順位の提案まではAIが行い、最終判断は常に人間（CEO）が行う設計に
なっています（`/morning-brief`が実例です）。

このプロジェクト自体が実験台です。会社OSに副業アイデアを実際に流し込み、
2026年7月4日、ブランド「LIMIT LAB WORKS」としてBOOTHショップを公開し、
最初の商品「AI Company OS Template Kit」を出品しました。ゼロから
「AIが社長を毎日支援する会社OS」を作っている過程を、このリポジトリと
下記のアカウントで公開しています。

- 🛍️ **BOOTH（ショップ）**: https://limit-lab.booth.pm/
- 🐦 **X（開発ログ）**: https://x.com/LimitLabJP
- 🐙 **GitHub**: LimitLabWorks

## これは何か

AIエージェントに「役職」を持たせ、それぞれに契約（Mission / Inputs /
Outputs / Authority / Cannot do / KPIs / Exit Criteria）を与えることで、
1人の人間（CEO）が複数のAI事業を同時に運営できる仕組みを目指しています。
案件は以下のパイプラインを通ります。

```
【発掘フェーズ】投資判断を作る
CEO／PM
 ▼
市場調査部 → 検証部 → 事業評価部 → CEO（Go/No-Go判断）

【実行フェーズ】承認された案件を利益に変える
CEO（承認）
 ▼
法務部 → 制作部 → マーケティング部 → 分析部 → 改善部
 │
 ▼
PM（結果を集約）
 ▼
CEO（次の経営判断: 継続・改善・撤退）
```

## ミッション

週末だけで開発可能な副業を継続的に生み出し、月5万円以上の副収入を
安定的に得ることを当面のミッションとする。詳細は `CLAUDE.md`（会社の
憲法）を参照。

## 開発方針

- 小さく作る（MVP）
- すぐ公開する
- 数字で判断する（Evidence First / Reality First）
- 失敗を記録する
- 改善を繰り返す

## 組織構造

CEO（経営・投資・撤退判断）を頂点に、PM（COO）が各部門にタスクを配分し、
成果をPortfolio Dashboardで一元管理する。

```
CEO（経営・投資・撤退判断）
        │
PM（COO・全案件統括・タスク配分）
        │
────────────────────
市場調査部
検証部
事業評価部
法務部
制作部
マーケティング部
分析部
改善部
────────────────────
        │
Portfolio Dashboard
```

## 主なドキュメント

- `LIMIT-OS.md` — 全ドキュメントを結ぶ地図（Why/Who/How/What）。
  迷ったらまずここ
- `CONSTITUTION.md` — LIMIT LAB憲法（最上位規範。Purpose/Mission/
  Vision/Values、信頼と信用・世のため人のため・先義後利・利用者第一・
  感動品質・技術は手段、Mission Check、Value Score）
- `CLAUDE.md` — 経営ルール（ミッション・経営理念・KPI階層・経営原則）
- `CEO.md` / `PM.md` — CEO・PM（COO）エージェント定義
- `Research.md` / `Validation.md` / `Evaluation.md` / `Production.md` /
  `Marketing.md` — 各部門のエージェント定義
- `docs/department-contracts.md` — 全役職の契約定義
- `docs/decision-framework.md` — 8軸スコアリング・5段階Go/No-Go判定
- `docs/portfolio-strategy.md` — 同時進行数の上限・Portfolio Rule・
  「No Internal Completion」原則
- `docs/channel-strategy.md` — 販売チャネル戦略（BOOTH/note/Gumroad/GitHub/X）
- `docs/human-desire-framework.md` — 人間理解のフレームワーク
  （欲求を作るのではなく理解し誠実に伝えるための分析ツール）
- `docs/growth-roadmap.md` — 90日ロードマップ
- `docs/opportunity-pipeline.md` — Idea→Research→Validation→Prototype→
  Pilot→Production→Growthの7ステージ
- `knowledge/Decision Log/` — 経営判断とその根拠の記録
- `knowledge/Institutional Memory/` — 再利用できる現場知見（効いたPrompt・
  失敗したWorkflow・CVRの高い販売ページ等）
- `knowledge/Performance Review/` — 各部門の月次振り返り
- `knowledge/Annual Reflection/` — Purpose/Visionへの到達度を振り返る年次記録
- `.claude/commands/` — Claude Code上でそのまま動くスラッシュコマンド一式
- `cases/` — 実際に会社OSへ投入した案件の記録（Research〜Marketingの
  実成果物）
- `knowledge/Lessons Learned/` — Sprintごとの振り返り（うまくいった
  ことも、いかなかったことも記録する）

## 最終目標

AIが副業アイデアを提案し、調査から検証・評価・制作・販売・改善まで
支援し、CEOが経営判断を下すことで、1人で複数のAI事業を同時に運営できる
「会社OS」を構築する。

まずは月5万円を目指しつつ、案件数と組織構造を拡張することで
月50万円・100万円規模まで自然にスケールできる土台を作る。
