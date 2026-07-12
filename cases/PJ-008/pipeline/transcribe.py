#!/usr/bin/env python3
"""自動字幕: faster-whisperで日本語を文字起こしし、テロップ用に整形した
SRTファイルを出力する。

事前準備（初回のみ）: pip install faster-whisper
使い方:
  python transcribe.py input_cut.mp4
  python transcribe.py input_cut.mp4 --model medium --max-chars 16

出力:
  input_cut.srt … 字幕ファイル（メモ帳で誤字を直してから焼き込みへ）

⚠️ このスクリプトは開発環境で未実行・未検証。初回実行がテストを兼ねる。
   モデルは初回に自動ダウンロードされる（small≒500MB, medium≒1.5GB）。
"""
import argparse, os, sys

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--model", default="small", help="tiny/small/medium。精度が欲しければmedium")
    ap.add_argument("--max-chars", type=int, default=18, help="テロップ1行の最大文字数")
    ap.add_argument("--gpu", action="store_true", help="NVIDIA GPU＋CUDA環境で高速化（未導入なら付けない）")
    a = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisperが未インストールです。実行: pip install faster-whisper"); sys.exit(1)

    # device="auto"はGPUを誤検出してcuBLAS(cublas64_12.dll)を要求し、
    # CUDA未導入のPCで落ちる。既定はCPUで確実に動かす（10分程度なら実用範囲）。
    # NVIDIA GPU＋CUDA環境なら --gpu で高速化できる。
    dev = "cuda" if a.gpu else "cpu"
    ct = "float16" if a.gpu else "int8"
    print(f"モデル{a.model}を{dev}で読み込み中（初回はダウンロードあり）...")
    model = WhisperModel(a.model, device=dev, compute_type=ct)
    segments, info = model.transcribe(a.input, language="ja", vad_filter=True)

    base, _ = os.path.splitext(a.input)
    out = f"{base}.srt"
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for seg in segments:
            n += 1
            f.write(f"{n}\n{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}\n")
            f.write(wrap(seg.text, a.max_chars) + "\n\n")
            print(f"  [{fmt_ts(seg.start)}] {seg.text.strip()}")
    print(f"\n完了: {out}（{n}区間）")
    print("次: メモ帳等でsrtの誤字を直す → README工程3の焼き込みコマンドへ")

if __name__ == "__main__":
    main()
