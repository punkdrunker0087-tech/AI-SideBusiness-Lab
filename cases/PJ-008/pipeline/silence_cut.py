#!/usr/bin/env python3
"""無音カット: ffmpegのsilencedetectで無音区間を検出し、発話区間だけを
つないだ動画を書き出す。

使い方:
  python silence_cut.py input.mp4
  python silence_cut.py input.mp4 --noise -35 --min-silence 0.6 --pad 0.15

出力:
  input_cut.mp4       … 無音を除去した動画
  input_segments.txt  … 採用した区間の一覧（確認用）

⚠️ このスクリプトは開発環境にffmpegが無いため未実行・未検証。
   初回実行がテストを兼ねる。エラーが出たらエラーメッセージごと
   AIに貼り付けて修正させること。
"""
import argparse, re, subprocess, sys, tempfile, os

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

def run_with_progress(cmd, label):
    """ffmpegを実行しつつ、進捗（time=...）を1行で表示し続ける"""
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         text=True, encoding="utf-8", errors="replace")
    log = []
    for line in p.stderr:
        log.append(line)
        m = re.search(r"time=(\d+:\d+:[\d.]+)", line)
        if m:
            print(f"\r{label} 処理位置 {m.group(1)} ...", end="", flush=True)
    p.wait()
    print()
    return p.returncode, "".join(log)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--noise", type=float, default=-35.0, help="無音とみなす音量(dB)。話し声が小さい素材は-40に")
    ap.add_argument("--min-silence", type=float, default=0.6, help="この秒数以上の無音だけカット")
    ap.add_argument("--pad", type=float, default=0.15, help="発話区間の前後に残す余白(秒)。ブツ切り感の調整")
    a = ap.parse_args()

    base, _ = os.path.splitext(a.input)

    # 1) 無音区間の検出
    print("工程1/3: 無音区間を検出中（動画の長さの半分〜同程度の時間がかかります）")
    _, log = run_with_progress(["ffmpeg", "-i", a.input, "-af",
               f"silencedetect=noise={a.noise}dB:d={a.min_silence}", "-f", "null", "-"],
               "  検出")
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", log)]
    ends   = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", log)]
    dur_m  = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log)
    if not dur_m:
        print("動画の長さが取得できませんでした。ffmpegの出力:\n" + log[-1500:]); sys.exit(1)
    total = int(dur_m.group(1))*3600 + int(dur_m.group(2))*60 + float(dur_m.group(3))

    # 2) 無音区間の補集合 = 発話区間（前後にpadを足す）
    silences = list(zip(starts, ends))
    keep, cur = [], 0.0
    for s, e in silences:
        seg_start = max(0.0, cur - a.pad) if cur > 0 else 0.0
        seg_end   = min(total, s + a.pad)
        if seg_end - seg_start > 0.05:
            keep.append((seg_start, seg_end))
        cur = e
    if cur < total:
        keep.append((max(0.0, cur - a.pad), total))
    if not keep:
        print("発話区間が見つかりません。--noise を -45 などに下げて再実行してください。"); sys.exit(1)

    with open(f"{base}_segments.txt", "w", encoding="utf-8") as f:
        for i, (s, e) in enumerate(keep):
            f.write(f"{i+1}\t{s:.2f}\t{e:.2f}\t({e-s:.2f}秒)\n")

    # 3) 区間ごとに切り出して連結（再エンコードで確実に）
    print(f"工程2/3: 発話区間{len(keep)}個を切り出し中")
    with tempfile.TemporaryDirectory() as td:
        listfile = os.path.join(td, "list.txt")
        with open(listfile, "w", encoding="utf-8") as lf:
            for i, (s, e) in enumerate(keep):
                print(f"\r  区間 {i+1}/{len(keep)} ...", end="", flush=True)
                part = os.path.join(td, f"p{i:04d}.mp4")
                r = run(["ffmpeg", "-y", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", a.input,
                         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                         "-c:a", "aac", "-b:a", "160k", part])
                if r.returncode != 0:
                    print(f"\n区間{i+1}の切り出しに失敗:\n" + r.stderr[-800:]); sys.exit(1)
                lf.write(f"file '{part}'\n")
        print("\n工程3/3: 連結中")
        r = run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                 "-c", "copy", f"{base}_cut.mp4"])
        if r.returncode != 0:
            print("連結に失敗:\n" + r.stderr[-800:]); sys.exit(1)

    cut_total = sum(e - s for s, e in keep)
    print(f"完了: {base}_cut.mp4")
    print(f"元: {total:.1f}秒 → 後: {cut_total:.1f}秒（{100*(1-cut_total/total):.0f}%短縮、区間{len(keep)}個）")
    print(f"区間一覧: {base}_segments.txt（カットされすぎなら --pad 0.3 で再実行）")

if __name__ == "__main__":
    main()
