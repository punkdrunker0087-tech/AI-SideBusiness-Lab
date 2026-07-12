# AI動画編集パイプライン — セットアップと実測手順

目的: 「AI動画編集が仕事になるか」を**実測**で判断するための最小
パイプライン。3工程（無音カット→自動字幕→焼き込み）をCEOのPCで動かし、
**人間時間が合計何分かかったか**を記録する。判定基準は
`cases/PJ-008/intake.md`に事前固定済み（実測後に動かさない）。

⚠️ **正直な注意**: スクリプト2本は開発環境にffmpegが無いため
**未実行・未検証**です。初回実行がテストを兼ねます。エラーが出たら
メッセージごとAIに貼り付けてください（それも実測時間に含めて記録）。

---

## 0. 事前準備（初回のみ・所要15分目安）

1. **ffmpeg**: https://ffmpeg.org/download.html から入手
   - Windows: 「ffmpeg release essentials」zipを展開→`bin`フォルダを
     PATHに追加。確認: ターミナルで `ffmpeg -version`
   - Mac: `brew install ffmpeg`
2. **Python 3.9+**: `python --version` で確認（無ければ python.org）
3. **faster-whisper**: `pip install faster-whisper`

## 1. 工程1: 無音カット

```
python silence_cut.py 素材.mp4
```
- 出力: `素材_cut.mp4`（無音除去済み）と区間一覧
- ブツ切り感が強い → `--pad 0.3`、カットされなさすぎ → `--noise -30`

## 2. 工程2: 自動字幕（SRT生成）

```
python transcribe.py 素材_cut.mp4 --model small
```
- 出力: `素材_cut.srt`
- **メモ帳でsrtを開き誤字を修正**（ここが人間の主作業。修正箇所数を数える）
- 精度不足なら `--model medium`（処理時間は増える）

## 3. 工程3: 字幕の焼き込み

```
ffmpeg -i 素材_cut.mp4 -vf "subtitles=素材_cut.srt:force_style='FontName=Meiryo,FontSize=20,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,MarginV=30'" -c:a copy 納品.mp4
```
- Macは `FontName=Hiragino Sans` に変更
- 黄色テロップにする場合: `PrimaryColour=&H33D3FF`（BGR順なので注意）

## 4. 実測記録（このファイルに追記していく）

計測ルール: ストップウォッチで**人間が手を動かしている時間だけ**を測る
（whisperの処理待ちは機械時間として別記録。待ち時間に他の作業をして
よいため）。

| 日付 | 素材の長さ | 工程1人間分 | 工程2人間分（誤字修正 n箇所） | 工程3人間分 | その他（試行錯誤・エラー対応） | 人間合計 | 機械待ち合計 | 納品水準か（自己評価） |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

## 5. 判定（intake.mdの事前固定基準）

- 人間合計 **45分以内** かつ手直し5箇所以内 → 受注テスト1件だけ実施
- **45〜90分** → 代行不成立。パイプライン商品化ルートを需要発掘SOPで検証
- **90分超** or 品質不足 → 棚上げ（記録をInstitutional Memoryへ）

## 責任分界（働き方プロトコルのリスク色分け）

- 🟢 AI: スクリプト修正・字幕整形ルール改善・実測記録の集計
- 🟡 AI下書き→CEO承認: 受注テストをする場合の出品文・料金表
- 🔴 CEOのみ: クラウドソーシングのアカウント運用・受注・クライアント
  連絡・納品・金銭授受
