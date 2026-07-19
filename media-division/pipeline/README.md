# ショート動画 全自動生成パイプライン（SOP）

実測日: 2026-07-19（Claude Codeリモート実行環境で全工程を実測済み。
サンプル2本生成: 無音12秒版 / AI社長音声つき21秒版）

## 成果物仕様

- 縦型 1080×1920 / H.264 mp4 / 30fps / AI音声ナレーション + 合成BGM
- 1本あたりの生成時間: 実測 約2〜3分（人間の作業ゼロ）

## 工程

```
① 台本作成（AI）
② 音声生成（TTS）→ 長さを実測
③ HTML/CSSで縦型画面を生成（音声の長さにタイムラインを同期）
④ Chromiumで録画（playwright-core, recordVideo 1080×1920）
⑤ ffmpegで mp4化 + 音声・BGM合成
⑥ 人間が確認 → 投稿（AI開示設定を忘れない）
```

## 環境セットアップ（リモート実行環境・毎セッション必要）

```bash
apt-get update && apt-get install -y ffmpeg          # フル版ffmpeg（Playwright付属版はVP8のみで不可）
npm i playwright-core                                 # ブラウザは /opt/pw-browsers/ の同梱Chromiumを使う
pip install edge-tts                                  # ニューラルTTS
cat /root/.ccr/ca-bundle.crt >> $(python3 -c "import certifi; print(certifi.where())")
                                                      # ↑プロキシCAをcertifiに追加（これがないとedge-ttsがTLSエラー）
# フォールバック（完全ローカルTTS・ネットワーク不要）:
apt-get install -y open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001
```

## 音声生成の選択肢（実測結果つき）

| 手段 | 品質 | この環境 | 商用利用の注意 |
|---|---|---|---|
| edge-tts（ja-JP-KeitaNeural 等） | ◎ ニューラル | ✅ 動作確認済み | Edgeブラウザ向け非公式利用。収益化運用に載せる前に正式なAzure TTS（従量課金・APIキー要）への移行を推奨 |
| Open JTalk | △ 機械的 | ✅ 動作確認済み（完全ローカル） | BSDライセンス系で制約少 |
| VOICEVOX（ずんだもん等） | ◎ キャラ音声 | ❌ この環境ではDL不可（GitHubアクセスがセッション登録リポジトリに制限されるため） | 人間のPCでは無料・クレジット表記（例「VOICEVOX:ずんだもん」）で商用可。キャラごとの利用規約を確認 |
| クラウドTTS（Azure/Google/ElevenLabs等） | ◎ | APIキー次第 | 有料。キーは人間が環境変数として設定（no-credentials-boundary準拠） |

## 実行例

```bash
# ② 音声
edge-tts --voice ja-JP-KeitaNeural --rate=+8% --text "（台本）" --write-media voice.mp3
ffprobe -v error -show_entries format=duration -of default=nw=1 voice.mp3   # → この秒数にHTMLの@keyframesを合わせる

# ④ 録画（record.mjs のwaitForTimeoutを音声長+1.5秒に）
node record.mjs

# ⑤ 合成（0.4秒の読み込みフラッシュをトリム、音声は0.3秒遅延、BGMは-30dB相当の合成パッド）
ffmpeg -y -ss 0.4 -i out/page@*.webm -i voice.mp3 \
  -f lavfi -i "aevalsrc=0.028*sin(2*PI*220*t)+0.022*sin(2*PI*261.63*t)+0.018*sin(2*PI*329.63*t):s=44100:d=DUR,afade=t=in:d=1.5,afade=t=out:st=DUR-2:d=2" \
  -filter_complex "[1:a]adelay=300|300,apad[v1];[v1][2:a]amix=inputs=2:duration=shortest:normalize=0[a]" \
  -map 0:v -map "[a]" -t DUR -c:v libx264 -pix_fmt yuv420p -r 30 -crf 20 -c:a aac -movflags +faststart out.mp4
```

## テンプレート

- `ceo-brief.html` — AI社長の朝礼テンプレート（21秒・5シーン構成）。
  台本を差し替える場合はシーンのテキストと`@keyframes`のタイミング%を
  音声区切りに合わせて調整する
- `record.mjs` — 録画スクリプト

## 人間がやること（このパイプラインの外側）

1. 内容の最終確認・承認
2. 投稿（各プラットフォームのAI生成開示設定を含む）
3. BGM・音声を差し替える場合の権利確認
4. TTSを正式運用に載せる際のライセンス判断（上表参照）
