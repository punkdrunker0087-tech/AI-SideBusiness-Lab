# PJ-003 市場調査成果物 — VRChat向けAI活用テンプレート・ワークフロー商品

作成: 市場調査部 / 2026-07-06
入力: 案件ID=PJ-003、案件名=VRChat向けAI活用テンプレート・ワークフロー商品、
案件概要=「VRChat向けAI活用テンプレート・ワークフロー商品（Claude Code
でVRChat制作を効率化するテンプレート、AIでアバター設定を自動化する
ワークフロー、VRChatクリエイター向けAIプロンプト集等）。既存LIMIT LAB
ブランドの新ジャンル展開案。ユーザー提案。」

---

## ① Executive Summary

VRChatの3Dアセット市場（BOOTH「3Dモデル」カテゴリ）は2025年に取扱高
約104億円（前年比+187%、利用者28.1万人・注文744万件）に達した巨大な
実市場であり、初心者のUnity/アバター設定の困難さも複数の一次情報で
裏付けられる実在の痛みである。一方で「Claude Code × VRChat」という
差別化軸には、無料OSSツール（UnityMCP-VRC）や海外Claude Code Skill
マーケットプレイス（mcpmarket.com）に既に類似の取り組みが存在しており、
「無料で手に入る技術」との差別化と、LIMIT LABが持たないUnity/3DCG専門性
の担保が成立条件になる。

## ② Problem

- VRChatのアバター改変・ワールド制作はUnity操作が前提だが、初心者には
  ハードルが高く、「モデリング完了からアップロードまで半年かかった」
  という体験談も存在する（Evidence 6）
- Avatar 3.0のパラメータ予算（256bit）、Quest向けパフォーマンスランク
  など、VRChat固有の技術制約への対応が難しい
- 既存の解決策（Modular Avatar等）はUnity操作の簡略化が中心で、
  「AIに相談しながら作る」体験を提供するものはまだ少ない

## ③ Customer

- **ペルソナ**: VRChatでアバター・ワールドを自作/改変したい個人クリエイター
  （Unity初心者〜中級者）。3Dモデリングはできるが実装・アップロード周りで
  つまずく層、逆にコードは書けるがVRChat固有仕様に不慣れな開発者層の両方
- **市場**: 日本語圏が中心（BOOTHの3Dモデルカテゴリの主戦場）。VRChat自体は
  Steam版だけでピーク7.8万人、直近30日平均約4.5万人の同時接続があり
  （Evidence 1）、日本ユーザー比率が高いとされる
- **利用シーン**: アバター改変・衣装調整・ワールドのギミック実装時に、
  Claude Codeで相談しながら作業する／既製テンプレートを使って時短する

`docs/human-desire-framework.md`に基づく分析:
- **Primary Desire**: 快適・利便性（Level 2） — 面倒なUnity設定・改変作業を
  楽にしたい
- **Secondary Desire**: 成長・達成（Level 3） — 自作アバター・ワールドを
  完成させて公開したい／承認・所属（Level 4） — VRChatコミュニティで
  自分の作品を認められたい

## ④ Evidence（最重要）

| # | 種類 | URL | 要約 | 信頼度（ランク） |
|---|---|---|---|---|
| 1 | プラットフォーム統計（activeplayer.io） | https://activeplayer.io/steam/vrchat | VRChatはSteam版で過去最高78,613同時接続を記録、直近30日平均約45,166人 | B |
| 2 | 業界レポート（pixiv公式） | https://www.pixiv.co.jp/2025/02/19/120000 | 「BOOTH 3Dモデルカテゴリ 取引白書2025」。2024年取扱高58億円超（前年比187%）、2025年は約104億円規模まで拡大。利用者21.8万人→28.1万人、注文件数402万件→774万件 | A |
| 3 | 業界メディア記事 | https://www.inside-games.jp/article/2026/02/06/177087.html | BOOTHの3Dモデルカテゴリ売上が100億円規模に達したと報道。主用途はVRChatアバター | C |
| 4 | プラットフォーム実データ（BOOTH商品ページ） | https://booth.pm/ja/items/8137605 | VRChatワールド制作支援ツール「ワールドつく～る」が¥2,500でBOOTH販売中。Unity初心者向けの実例商品 | B |
| 5 | 個人体験記（note） | https://note.com/pichikyo/n/nfe806dde550a | Blender初心者がClaude Code頼みで6個のツール（ChatGPT・TRIPO 3D・Blender・Mixamo・Unity等）を繋ぎ、1日でVRChatアバターを完成させた実例 | D |
| 6 | 個人体験記（ブログ/note、複数） | https://vrnavi.jp/vrchat-unity/ | Unity初心者のアバター改変が難しく、モデリング完了から販売可能になるまで約半年かかった例など、初心者のUnity習得障壁が繰り返し語られている | D |
| 7 | GitHubリポジトリ | https://github.com/swax/UnityMCP-VRC | Claude経由でUnityを直接操作しVRChatワールド/UdonSharpを開発するMCPサーバー。無料OSS、スクリーンショット取得・オブジェクト操作等の機能を持つ | B |
| 8 | マーケットプレイス（mcpmarket.com） | https://mcpmarket.com/tools/skills/vrchat-avatar-builder | 「VRChat Avatar Builder」等、Avatar 3.0のパラメータ予算・パフォーマンスランク最適化を扱うClaude Code Skillが複数出品されている（Avatar Builder／Avatar Development／World Building／UdonSharp Codingの4種確認） | B |
| 9 | 個人体験記（note） | https://note.com/sechiro_vrc/n/n1705a7330377 | 個人開発者がCodex（AIコーディングエージェント）向けにVRChatワールドギミック開発用Skillを無料公開 | D |
| 10 | 業界メディア記事（MoguLive） | https://www.moguravr.com/world-tsukuru-vrchat-tool-release/ | 「ワールドつく～る」のリリースを報じる記事。Unity初心者でも手軽にVRChatワールドを作れる点を訴求ポイントとして紹介 | C |

Evidence Ranking Aに該当する一次情報として、BOOTH運営元pixiv社自身が
公開した公式白書（Evidence 2）を確保できており、市場規模については
PJ-001・PJ-002より一次情報に近い。一方で「AI×VRChat」という差別化軸の
競合状況（Evidence 7・8・9）は無料公開が中心で、有料需要の実証はまだ弱い。

## ⑤ Competitors

| 会社・商品 | 価格 | 特徴 | 弱点 | 差別化余地 |
|---|---|---|---|---|
| UnityMCP-VRC（GitHub, swax） | 無料（OSS） | ClaudeからUnity Editorを直接操作しVRChatワールド/UdonSharpを開発するMCPサーバー | MCPサーバーのセットアップ自体に技術知識が必要、パッケージ化された商品ではない | セットアップ不要ですぐ使えるプロンプト集・チェックリストとして日本語で再パッケージ |
| mcpmarket.com「VRChat Avatar Builder」等 | 価格情報なし（海外マーケットプレイス、英語） | Avatar 3.0のパラメータ予算・パフォーマンスランク最適化など専門的なClaude Code Skill | 英語中心、BOOTH等の日本語圏VRChatクリエイターには認知度が低い | 日本語BOOTH経由での販売、LIMIT LABブランドの信頼を通じた訴求 |
| ワールドつく～る（BOOTH, はむんちゅ） | ¥2,500 | Unity初心者向けワールド制作支援ツール（GUIカタログ・ワンクリックギミック設置） | AIではなく手動GUIツール、ワールド制作限定（アバターは対象外） | AI（Claude Code）との対話型ワークフローで差別化、アバター・ワールド両対応 |
| 個人クリエイターの改変ガイド/情報コンテンツ（note等） | 無料〜数百円 | 「アバター改変なび」等、初心者向けの手順解説記事が多数存在 | 断片的・単発の情報が中心で、体系的なテンプレート・チェックリストになっていない | Research/Evaluation部で培った「体系化・テンプレート化」のノウハウを転用 |
| 3D AI Studio / Tripo AI（海外SaaS） | サブスクリプション制（$/月、要問合せ） | 画像からアバターを自動生成・自動リギングするAIツール | アバター生成SaaSであり、VRChat固有のセットアップ・最適化ノウハウの提供が主目的ではない | 「生成」ではなく「既存アバター・ワールドの制作効率化」に特化したテンプレート/プロンプト路線で棲み分け |

## ⑥ TAM/SAM/SOM（概算）

- **TAM**: BOOTH「3Dモデル」カテゴリ全体で年間約104億円（2025年、Evidence 2）。
  VRChat関連アセット全般（アバター・衣装・ワールド・ギミック等）がこの
  大半を占めると推定される
- **SAM**: 「AI活用・制作効率化」に限定したセグメント。UnityMCP-VRC・
  mcpmarket.com上のVRChat向けSkillが複数存在すること（Evidence 7・8）
  から需要の芽はあるが、正確な市場規模データはなく、TAMに対してごく
  一部（推定で数千万円規模以下）にとどまると見られる
- **SOM**: 個人・週末稼働で狙える現実的な初年度規模は、既存商品ライン
  （Starter ¥480〜Standard ¥980）の価格帯を踏襲した場合、月数千円〜
  数万円規模からのスタートが妥当。PJ-002のような「テンプレート一式」の
  実績なしに大きな規模を見込むのはEvidence不足

## ⑦ Business Model（収益モデル候補3案）

1. **単品テンプレート/プロンプト集販売** — 「VRChatアバター改変チェック
   リスト」「Claude Code向けUdonSharpプロンプト集」等をBOOTHで¥480〜
   ¥980で販売。既存の商品ライン（Starter/Standard）にそのまま乗せられ、
   検証速度が最も速い
2. **Bundle型（スターターキット）** — 「VRChat制作AI活用スターター
   キット」として複数テンプレート＋チェックリストを¥1,980でまとめ
   販売。PJ-002の「Business Template Factory」と同じBundle戦略を転用
3. **体験記事＋テンプレートのセット** — 「Claude CodeでVRChatアバターを
   1日で作った話」のようなnote記事（集客）から、実際に使えるテンプレ
   ート販売への導線を作る。Evidence 5のような実例が既に個人ベースで
   存在し、需要の裏付けがある

## ⑧ Risks

1. 無料OSS（UnityMCP-VRC）や海外Skillマーケットプレイス（mcpmarket.com）
   に類似の取り組みが既に存在し、「無料で手に入る」ものに料金を払わせる
   差別化が必要（Evidence 7・8）
2. LIMIT LABはこれまでUnity/3DCG/VRChat固有仕様（Avatar 3.0パラメータ
   予算・Quest最適化等）の専門実績がなく、内容の正確性・品質を担保
   できるかが未検証
3. VRChat SDK・Unityバージョン・Avatar仕様は頻繁に更新されるため、
   一度作ったテンプレートが陳腐化しやすく、「Build Once, Sell Many」
   前提が崩れやすい（継続メンテナンスコストが他商品より高い）
4. VRChatの利用規約・アセットの商用利用条件、Unity Asset Storeの
   ライセンス条件など、法務確認が必須の論点が他商品より多い
5. 既存X/note読者は「AI会社OS開発ログ」というポジショニングで集まって
   おり、VRChatへのジャンル拡張はブランドの一貫性を薄める可能性がある
   （Brand Guardianの観点で要確認）
6. 市場価格帯が¥300〜¥2,500と低廉で、既存Standard価格（¥980）を
   維持できても客単価を大きく上げにくい

## ⑨ AI Fit

- **自動化率**: 中程度。プロンプト集・チェックリスト・解説テンプレート
  自体の文章生成はAIで完結できるが、「実際にUnity/VRChatで動作するか」
  の実機検証はAIエージェント単体では行えない
- **必要API**: 特になし（LIMIT LAB側はClaude Codeでの文書生成のみ。
  UnityMCP等の実機操作ツールは対象外）
- **必要LLM**: Claude（Claude Code）
- **必要工数**: 既存の業務テンプレート系商品より高い。VRChat/Unity固有
  仕様の調査・正確性検証に追加コストがかかる
- **AI実現可能性**: 中程度。ドキュメント・プロンプト集としてのAI生成は
  可能だが、品質保証には人間（CEO）による実機確認が必要になる可能性が
  高く、他の会社OS派生商品より人手依存度が高い

## ⑩ Recommendation

**Conditional Go**

- 市場規模（BOOTH 3Dモデルカテゴリ104億円、Evidence 2）と初心者の
  実在するペイン（Evidence 5・6）は強く裏付けられており、事業機会
  としては有望
- ただし、(a) 無料の直接競合（UnityMCP-VRC、mcpmarket.com）が既に存在
  すること、(b) LIMIT LABにUnity/VRChat固有の専門実績がないこと、
  (c) 既存ブランド・読者層との整合性（Brand Guardian観点）の3点が
  未検証のため、無条件のGoは推奨しない
- 条件: まずSoftware実装や3DCG専門性を要さない「Content/Template型」
  （例: Claude Code向けUdonSharpプロンプト集、Unity設定チェックリスト）
  に限定した単一の低価格商品（¥480〜¥980）で市場の実反応を検証し、
  Value Score・実売上が確認できてからサブブランド化やライン拡張を検討する

最終的なGo/No-Go判断は事業評価部のスコアリングを経てCEOが行う。

## Confidence Score

- Evidence: ★★★★☆
- 市場規模（TAM/SAM/SOM）: ★★★★★（pixiv公式白書という一次情報を確保）
- 競合: ★★★★☆
- **総合信頼度: 75%**（市場規模の裏付けは強いが、「AI×VRChat」という
  差別化軸自体の有料需要・LIMIT LAB側の専門性については未検証要素が
  残るため、PJ-002（80%）よりやや低い信頼度とした）

---

## Quality Gate（Definition of Done）

- [x] Executive Summary
- [x] Problem
- [x] Customer
- [x] Evidence 5件以上（10件）
- [x] Competitors 5件以上（5件）
- [x] TAM/SAM/SOM
- [x] Business Model
- [x] Risks（6項目）
- [x] AI Fit
- [x] Recommendation
- [ ] 検証部レビュー（PASS判定）

Quality Gateの実質項目はすべて達成。検証部レビューは `/validate` 実行時に
行う。
