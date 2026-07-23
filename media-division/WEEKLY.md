# 週次まとめ動画 SOP（EXP-008）

制定: 2026-07-24（CEO指示: 週1回のまとめ動画を投稿したい）

`BRAND.md`のコンテンツ4役割のうち**Depth（深い理解）**を担う動画。
毎日のショートが「今日」を記録するのに対し、週次動画は「今週」を
振り返り、視聴者を研究の同伴者にする。

## 仕様

- **形式**: 通常動画（Shortsではない）・3〜5分
- **投稿タイミング**: Day 7の倍数（Day 7・14・21・28）に毎週
- **対象期間**: 直近7日分（例: Week1はDay1〜7）
- **サムネイル必須**: 通常動画はShortsと違い動画フレームの自動サムネに
  頼れない。`pipeline/weekly/`でHTML/CSSから1280×720のサムネイルを生成する
  （実写・写真は使わずブランド配色のテキストベース）

## 台本構成（6パート）

1. **オープニング**: 今週の全体像（例: 「Week1、5本の実録を公開した」）
2. **今週の実験**: その週に登録・進行したEXP番号と結果を列挙
3. **今週の数字**: 視聴回数の推移、L2介入率・AI開示設定の定着状況など
4. **今週いちばんの発見**: EXPERIMENTS.md/OBSERVATIONS.mdから象徴的な
   1件を選ぶ（例: Week1ならEXP-006のフォント発見）
5. **来週やること**: 進行中の実験・保留事項（例: EXP-007の効果測定）
6. **クロージング**: 「今日のOSは〜」の日次一行に対応する週次の一文
   （例: 「今週のOSは、どこで現実とぶつかったか」）

## ソース

- `EXPERIMENTS.md`（対象週のEXP項目）
- `OBSERVATIONS.md`（Observation項目）
- `REJECTION-LOG.md`
- `days/day-0N/report.md`（対象週の7日分）

## 生成方法

台本はショートと同じ`pipeline/make-short-cloud.mjs`＋`voicevox-local/
template.html`を流用できる（シーン数を増やし尺を伸ばすだけで技術的な
変更は不要）。サムネイルのみ専用パイプライン:

```bash
cd media-division/pipeline/weekly
node make-thumbnail.mjs thumb.json thumbnail.png
```

`thumb.json`の形式:
```json
{
  "week": "WEEK 1",
  "headline": "見出し（<span class=\"accent\">...</span>で強調可）",
  "stats": [{"num": "5", "label": "本の実録"}, {"num": "0.7%", "label": "介入率まで低下"}]
}
```

## Brand Guardian追加チェック（週次のみ）

通常のチェックリストに加えて:

- [ ] 複数日のデータを正確に集計しているか（誇張・切り取りがないか）
- [ ] その週に起きた不都合な事実（失敗・伸び悩み）も含めているか
  （良い話だけをまとめていないか）
- [ ] サムネイルの数値が本編・台帳の実測値と一致しているか（Promise Gap防止）

## ディレクトリ構成

```
media-division/weeks/week-01/
  scenario.json      台本
  thumb.json         サムネイル用データ
  thumbnail.png      生成済みサムネイル
  week1.mp4           動画本体
  publish.md         投稿パッケージ
  report.md           週次報告
```
