# VOICEVOXローカル実行キット（人間のPC用）

## なぜこれが必要か（EXP-003の結論）

AI社員が動くクラウド実行環境と、あなたのPCは**別のマシン**。
PCにVOICEVOXをインストールしても、クラウド側からは接続できない
（127.0.0.1はそれぞれ自分自身を指す）。

したがってVOICEVOXのキャラ音声を使う場合の分業は:

```
クラウド（AI社員）: 台本・HTMLテンプレート・タイミング設計・SOP整備
あなたのPC（人間）: 音声合成（このキット）→ 録画 → 合成 → 確認 → 投稿
```

音声だけクラウドで完結させたい日は、edge-tts版パイプライン（`../README.md`）を
そのまま使えばよい。**VOICEVOX=キャラ声が欲しい日のローカル手順**がこのキット。

## PC側の初回セットアップ（1回だけ）

1. [VOICEVOX](https://voicevox.hiroshiba.jp/) をインストールして起動
   （起動中はエンジンが `127.0.0.1:50021` で待機する）
2. [Node.js](https://nodejs.org/)（v18以上）と [ffmpeg](https://ffmpeg.org/) をインストール
3. このリポジトリをclone
4. `media-division/pipeline/` で `npm i playwright-core` と
   `npx playwright install chromium` を実行

## 動画1本の作り方（全自動・推奨）

```bash
cd media-division/pipeline/voicevox-local
npm i playwright && npx playwright install chromium   # 初回のみ
node make-short.mjs                                    # scenario.json から out.mp4 を生成
```

`make-short.mjs` がシーンごとのTTS→音声の実測秒数でタイムライン自動同期→
録画→合成まで一括で行う。台本を変えるときは `scenario.json` を差し替える
だけでよい（タイミング調整は不要）。

## 動画1本の作り方（手動・仕組みを理解したい人向け）

```bash
cd media-division/pipeline

# ① 接続確認と話者一覧
curl http://127.0.0.1:50021/version
curl http://127.0.0.1:50021/speakers   # 使いたいキャラのstyle idを控える

# ② 音声合成（例: ずんだもん=3）
node voicevox-local/voicevox.mjs "おはようございます。AI社長なのだ。" voice.wav 3

# ③ 音声の長さを確認 → HTMLテンプレートの@keyframesを合わせる
ffprobe -v error -show_entries format=duration -of default=nw=1 voice.wav

# ④ 録画（record.mjs内のwaitForTimeoutを音声長+1.5秒に。
#    PCではexecutablePathの行を削除しplaywright標準のchromiumで動く）
node record.mjs

# ⑤ 合成（DURを③の秒数に置換）
ffmpeg -y -ss 0.4 -i out/page@*.webm -i voice.wav \
  -filter_complex "[1:a]adelay=300|300,apad[a]" \
  -map 0:v -map "[a]" -t DUR -c:v libx264 -pix_fmt yuv420p -r 30 -crf 20 \
  -c:a aac -movflags +faststart out.mp4
```

## 運用ルール

- **クレジット表記必須**: 概要欄・動画内に「VOICEVOX:（キャラ名）」を記載
- キャラごとの利用規約を初回に確認する（商用可否・禁止事項）
- 台本とHTMLはAI社員がクラウド側で用意し、このキットの実行だけが人間の作業
