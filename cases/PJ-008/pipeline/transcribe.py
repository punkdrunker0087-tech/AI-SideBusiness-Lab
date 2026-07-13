#!/usr/bin/env python3
"""自動字幕: faster-whisperで日本語を文字起こしし、テロップ用に整形した
SRTファイルを出力する。語ごとのタイムスタンプも取得し、style_subtitle.py
での単語カラオケ強調に使う _words.json を書き出す。

事前準備（初回のみ）: pip install faster-whisper
使い方:
  python transcribe.py input_cut.mp4
  python transcribe.py input_cut.mp4 --fast                 # 精度より速度
  python transcribe.py input_cut.mp4 --terms "限界ラボ,BOOTH"  # 固有名詞のヒント
  python transcribe.py input_cut.mp4 --translate            # 英語字幕も生成

出力:
  input_cut.srt         … 字幕（メモ帳で誤字を直してから焼き込みへ）
  input_cut_words.json  … 語ごとのタイムスタンプ（style_subtitle.pyが読む）
  input_cut_en.srt      … （--translate時のみ）英語字幕

⚠️ このスクリプトは開発環境で未実行・未検証。初回実行がテストを兼ねる。
   モデルは初回に自動ダウンロードされる（small≒500MB, medium≒1.5GB）。
"""
import argparse, json, os, sys

def fmt_ts(sec):
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

def wrap(text, max_chars):
    # 日本語テロップ用: 読点・スペースを優先しつつmax_charsで折り返し(最大2行)
    text = text.strip()
    if len(text) <= max_chars:
        return text
    cut = max_chars
    for i in range(max_chars, max(0, max_chars - 6), -1):
        if text[i-1] in "、。！？ 　,.!?":
            cut = i; break
    return text[:cut] + "\n" + text[cut:cut + max_chars]

def group_words_into_cues(words, min_dur=1.2, max_dur=6.0,
                           max_chars_per_line=15, max_lines=2, pause_gap=0.6):
    """語のタイムスタンプ列を、字幕1画面ぶんのキューにまとめ直す。
    元のwhisperセグメントより細かい制御ができる（最短/最長・文字数上限・
    自然なポーズでの区切り）。全角文字は1文字=1として概算する。"""
    max_total_chars = max_chars_per_line * max_lines
    groups, cur = [], []
    for w in words:
        gap = (w["start"] - cur[-1]["end"]) if cur else 0.0
        cur_chars = sum(len(x["word"]) for x in cur)
        would_exceed_chars = cur and (cur_chars + len(w["word"]) > max_total_chars)
        would_exceed_dur = cur and (w["end"] - cur[0]["start"] > max_dur)
        natural_pause = cur and (gap > pause_gap)
        if cur and (would_exceed_chars or would_exceed_dur or natural_pause):
            groups.append(cur); cur = []
        cur.append(w)
    if cur:
        groups.append(cur)

    cues = []
    for g in groups:
        start, end = g[0]["start"], g[-1]["end"]
        if end - start < min_dur:
            end = start + min_dur
        cues.append({"start": start, "end": end, "words": g})
    # 1フレーム未満の隙間（無音による一瞬の点滅）を詰める
    for i in range(len(cues) - 1):
        gap = cues[i + 1]["start"] - cues[i]["end"]
        if 0 < gap < 0.08:
            cues[i]["end"] = cues[i + 1]["start"]
    return cues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--model", default="medium", help="tiny/small/medium/large-v3。既定medium（精度優先）")
    ap.add_argument("--fast", action="store_true", help="精度より速度。--modelの指定を上書きしsmallを使う")
    ap.add_argument("--max-chars", type=int, default=15, help="テロップ1行の最大文字数（目安13〜16）")
    ap.add_argument("--terms", default="", help="固有名詞・専門用語のヒント（カンマ区切り）。誤変換対策")
    ap.add_argument("--gpu", action="store_true", help="NVIDIA GPU＋CUDA環境で高速化（未導入なら付けない）")
    ap.add_argument("--translate", action="store_true", help="英語翻訳字幕(_en.srt)も生成する")
    a = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisperが未インストールです。実行: pip install faster-whisper"); sys.exit(1)

    model_name = "small" if a.fast else a.model
    # device="auto"はGPUを誤検出してcuBLAS(cublas64_12.dll)を要求し、
    # CUDA未導入のPCで落ちる。既定はCPUで確実に動かす。
    dev = "cuda" if a.gpu else "cpu"
    ct = "float16" if a.gpu else "int8"
    print(f"モデル{model_name}を{dev}で読み込み中（初回はダウンロードあり。medium≒1.5GB）...")
    model = WhisperModel(model_name, device=dev, compute_type=ct)

    prompt = "、".join(t.strip() for t in a.terms.split(",") if t.strip()) or None
    segments, info = model.transcribe(
        a.input, language="ja", vad_filter=True,
        word_timestamps=True, initial_prompt=prompt)

    base, _ = os.path.splitext(a.input)
    words = []
    seg_count = 0
    for seg in segments:
        seg_count += 1
        for w in (seg.words or []):
            token = w.word.strip()
            if token:
                words.append({"start": w.start, "end": w.end, "word": token})
        print(f"  [{fmt_ts(seg.start)}] {seg.text.strip()}")

    out = f"{base}.srt"
    words_out = f"{base}_words.json"

    if words:
        cues = group_words_into_cues(words, max_chars_per_line=a.max_chars)
        with open(out, "w", encoding="utf-8") as f:
            for i, c in enumerate(cues, 1):
                text = "".join(w["word"] for w in c["words"])
                f.write(f"{i}\n{fmt_ts(c['start'])} --> {fmt_ts(c['end'])}\n")
                f.write(wrap(text, a.max_chars) + "\n\n")
        # _words.json: 各語がどのSRTキュー(0始まり)に属するかを記録する。
        # 元のwhisperセグメント番号ではなく、上のcue分割後の番号を使う
        # ——style_subtitle.pyがSRTの行番号とそのまま突き合わせられるため。
        rows = []
        for ci, c in enumerate(cues):
            for w in c["words"]:
                rows.append({"cue": ci, "start": w["start"], "end": w["end"], "word": w["word"]})
        with open(words_out, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print(f"\n完了: {out}（{len(cues)}区間、元セグメント{seg_count}個から再分割）")
        print(f"完了: {words_out}（語{len(rows)}件、抑揚づけ用）")
    else:
        # word_timestampsが取れなかった場合の後方互換フォールバック
        print("⚠️ 語ごとのタイムスタンプが取得できませんでした。セグメント単位で出力します。")
        segments2, _ = model.transcribe(a.input, language="ja", vad_filter=True, initial_prompt=prompt)
        n = 0
        with open(out, "w", encoding="utf-8") as f:
            for seg in segments2:
                n += 1
                f.write(f"{n}\n{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}\n")
                f.write(wrap(seg.text, a.max_chars) + "\n\n")
        print(f"完了: {out}（{n}区間、_words.jsonなし＝style_subtitle.pyは静的強調にフォールバック）")

    # --translate: 英語字幕も生成（whisperのtranslateタスク＝ローカル・無料）
    if a.translate:
        en = f"{base}_en.srt"
        print("英語翻訳字幕を生成中（task=translate）...")
        segs_en, _ = model.transcribe(a.input, task="translate", vad_filter=True)
        m = 0
        with open(en, "w", encoding="utf-8") as f:
            for seg in segs_en:
                m += 1
                f.write(f"{m}\n{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}\n")
                f.write(seg.text.strip() + "\n\n")
        print(f"完了: {en}（{m}区間）")

    print("次: メモ帳等でsrtの誤字を直す → style_subtitle.pyで抑揚をつける")

if __name__ == "__main__":
    main()
