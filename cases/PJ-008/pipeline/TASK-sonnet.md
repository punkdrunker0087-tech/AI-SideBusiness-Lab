# 実装タスク（Sonnet 5向け）— 動画字幕を「一流編集者」水準へ

委任元: CEO / 2026-07-12。working-method.md 委任4条件を満たす単一課題。
着手前に `style-win-condition.md`（勝利条件・地雷・60点採点）を必ず読む。
見栄えはffmpeg無しのAI環境で確認不可 → 最終判定はCEOのレンダリング目視。

## 現状（読むファイル）
- `transcribe.py`: whisper文字起こし → SRT。`--translate`で英語SRT
- `style_subtitle.py`: SRT → ASS（フェード＋キーワード強調・1画面最大2個）
- 実測所見（`README.md`「決定的な発見」）: 精度と人間時間は良好、
  しかし「全字幕が同一・抑揚なし」。競合(Vrew/CapCut)は無料で高精度 →
  **単なる自動字幕では勝てない。抑揚と精度の作り込みが唯一の差別化**

## やること（2領域）

### A. 精度（transcribe.py）
1. 既定modを `small`→`medium`（`--fast`でsmallに戻せる）
2. `word_timestamps=True` を有効化し、語ごとの start/end を取得
3. 出力を SRT に加えて **`_words.json`**（[{start,end,word,seg_id}]）も書く
4. `--terms "固有名詞1,固有名詞2"` を `initial_prompt` に渡し誤変換を減らす
5. 字幕分割の改善: 1行=全角13〜16字・1画面最大2行・1cue最短1.2秒
   最長6秒・cue間の無音は詰める（1フレ点滅を作らない）

### B. 抑揚（style_subtitle.py、`_words.json`があれば使う）
1. **語ごとカラオケ強調**（本命）: ASSの `\kf` で発話に合わせ語が
   進行ハイライト。Style は SecondaryColour=白 / PrimaryColour=黄
   `&H0033D3FF`。各語 `{\kf<持続センチ秒>}語`。持続=word.end-start
2. 強調語（数字・「」・指定語）は追加で `\fs`拡大（既存ロジック流用、
   1画面最大2個の上限は維持）
3. 入場に軽い動き: `\fad(120,60)` ＋ 強調語に一瞬の拡大
   `\t(0,150,\fscx115\fscy115)\t(150,300,\fscx100\fscy100)`
4. `_words.json` が無ければ現行の静的強調にフォールバック（後方互換）

## 完了条件（自己チェック可能）
- [ ] `python transcribe.py sample_cut.mp4 --translate` が SRT/_en.srt/
      _words.json を生成（構文・JSON妥当性をスクリプトで確認）
- [ ] `python style_subtitle.py sample_cut.srt` が ASS を生成し、
      内部自己検査（カンマ数・波括弧対応・タイムスタンプ）を全通過
- [ ] scratchpadのサンプルSRT/JSONで生成ロジックを実測（visualでなく
      **ファイル構造の正しさ**を確認・ログを残す）
- [ ] 既存の「1画面最大2個」「ブランド黄限定」の地雷回避を壊していない

## 完了後レポート（短く）
- 変更点3行 / 実測ログの要点 / CEOがレンダリングで見るべき確認点3つ
- CEOが `style-win-condition.md` の60点判定を下せる状態にして返す

## リスク色分け（working-method）
- 🟢 Sonnet単独可: スクリプト実装・サンプルでの構造検証・ドキュメント
- 🟡 CEO承認: 出品・料金・対外文言（このタスクの範囲外）
- 🔴 禁止: 認証情報・本番公開・金銭（このタスクに含めない）
