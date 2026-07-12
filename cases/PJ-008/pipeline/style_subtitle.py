#!/usr/bin/env python3
"""字幕スタイリング: transcribe.pyが出したSRTを読み、フェードイン＋
キーワード強調をつけたASS字幕を生成する。「字幕が全部同じで抑揚が
つかない」への対策（PJ-008 style-win-condition.md）。

使い方:
  python style_subtitle.py 素材_cut.srt
  python style_subtitle.py 素材_cut.srt --keywords "AI,自動化,効率化"
  python style_subtitle.py 素材_cut.srt --res 1080   # 720/1080/2160

出力:
  素材_cut.ass … 焼き込み用のスタイル付き字幕

焼き込み（README工程参照）:
  ffmpeg -i 素材_cut.mp4 -vf "ass=素材_cut.ass" -c:a copy 完成.mp4

⚠️ 見栄えはAIが確認できない（開発環境にffmpeg無し）。生成物の構造
   正しさのみ検証済み。最終判定はレンダリング＋目視で。
"""
import argparse, re, sys, os

# ブランド配色（ASSは &HAABBGGRR = alpha,blue,green,red の順）
ACCENT = r"&H0033D3FF"   # 黄 #ffd333
WHITE  = r"&H00FFFFFF"

def srt_time_to_ass(t):
    # "00:01:02,345" -> "0:01:02.34"
    m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)", t.strip())
    if not m: return None
    h, mi, s, ms = m.groups()
    cs = round(int(ms.ljust(3, "0")[:3]) / 10)   # ミリ秒→センチ秒
    if cs >= 100: cs = 99
    return f"{int(h)}:{int(mi):02d}:{int(s):02d}.{cs:02d}"

def parse_srt(text):
    text = text.replace("﻿", "").replace("\r\n", "\n")
    blocks = re.split(r"\n\s*\n", text.strip())
    cues = []
    for b in blocks:
        lines = [l for l in b.split("\n") if l.strip()]
        if len(lines) < 2: continue
        ti = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if ti is None: continue
        a, _, z = lines[ti].partition("-->")
        start, end = srt_time_to_ass(a), srt_time_to_ass(z)
        if not start or not end: continue
        body = " ".join(lines[ti+1:]).strip()
        if body: cues.append((start, end, body))
    return cues

MAX_EMPH_PER_CUE = 2   # 1画面での強調は最大2個（全部強調=どれも目立たない、を防ぐ）

def find_emphasis_spans(text, user_keywords):
    """強調すべき区間を優先度つきで集め、1字幕あたり最大MAX個に絞る。
    優先度: 指定語(3) > 数字+単位(2) > 「」内(2) > 長いカタカナ(1)。
    カタカナは日本語で頻出しすぎるため最下位＋長さ条件を厳しめに。"""
    cand = []  # (start, end, priority)
    for kw in user_keywords:
        kw = kw.strip()
        if not kw: continue
        for m in re.finditer(re.escape(kw), text):
            cand.append((m.start(), m.end(), 3))
    for m in re.finditer(r"[0-9０-９]+(?:[.,][0-9０-９]+)?(?:円|割|分|秒|時間|人|件|%|％|倍|回|万|億|台|個|本|日|年|月|週)?", text):
        if len(m.group()) >= 2:
            cand.append((m.start(), m.end(), 2))
    for m in re.finditer(r"[「『]([^」』]{1,20})[」』]", text):
        cand.append((m.start(1), m.end(1), 2))
    for m in re.finditer(r"[ァ-ヴー]{4,}", text):   # 4文字以上に厳格化
        cand.append((m.start(), m.end(), 1))

    # 優先度の高い順・長い順に採用し、重なりは捨てる。最大MAX個。
    cand.sort(key=lambda x: (-x[2], -(x[1]-x[0])))
    chosen = []
    for s, e, _ in cand:
        if any(not (e <= cs or s >= ce) for cs, ce in chosen):
            continue  # 既採用と重なる
        chosen.append((s, e))
        if len(chosen) >= MAX_EMPH_PER_CUE:
            break
    return sorted(chosen)

def build_text(body, user_keywords, big):
    """本文に強調のインラインタグを挿入。\r でスタイル既定へ戻す。"""
    spans = find_emphasis_spans(body, user_keywords)
    if not spans:
        return body
    out, cur = [], 0
    for s, e in spans:
        out.append(body[cur:s])
        seg = body[s:e]
        out.append(f"{{\\fs{big}\\c{ACCENT}}}{seg}{{\\r}}")
        cur = e
    out.append(body[cur:])
    return "".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="transcribe.pyが出した .srt")
    ap.add_argument("--keywords", default="", help="強調したい語をカンマ区切りで（任意）")
    ap.add_argument("--res", type=int, default=1080, choices=[720, 1080, 2160],
                    help="動画の縦解像度。字幕サイズの基準")
    a = ap.parse_args()

    if not os.path.exists(a.input):
        print(f"ファイルが見つかりません: {a.input}"); sys.exit(1)
    cues = parse_srt(open(a.input, encoding="utf-8").read())
    if not cues:
        print("SRTから字幕が読めませんでした。transcribe.pyの出力を確認してください。"); sys.exit(1)

    # 解像度に応じた基準サイズ
    playres = {720: (1280, 720), 1080: (1920, 1080), 2160: (3840, 2160)}[a.res]
    base_fs = {720: 40, 1080: 56, 2160: 108}[a.res]
    big_fs  = round(base_fs * 1.45)
    keywords = a.keywords.split(",") if a.keywords else []

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {playres[0]}
PlayResY: {playres[1]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Meiryo,{base_fs},{WHITE},&H000000FF,&H00101A2B,&H64000000,1,0,0,0,100,100,0,0,1,{max(2,base_fs//18)},1,2,80,80,{base_fs},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines, emphasized = [], 0
    for start, end, body in cues:
        styled = build_text(body, keywords, big_fs)
        if "\\fs" in styled: emphasized += 1
        text = "{\\fad(150,80)}" + styled
        lines.append(f"Dialogue: 0,{start},{end},Base,,0,0,0,,{text}")

    out_path = os.path.splitext(a.input)[0] + ".ass"
    content = header + "\n".join(lines) + "\n"

    # --- 自己検査（構造の正しさ。見栄えではない） ---
    problems = []
    for i, l in enumerate(lines):
        head, _, txt = l.partition(",,")   # Nameの後ろ
        # Dialogue行のフィールド数（Text手前まで9カンマ）を確認
        if l.count(",") < 9: problems.append(f"{i}: フィールド不足")
        if txt.count("{") != txt.count("}"): problems.append(f"{i}: 波括弧の非対応")
    if problems:
        print("⚠️ 生成物に構造上の問題:\n  " + "\n  ".join(problems[:5])); sys.exit(1)

    open(out_path, "w", encoding="utf-8").write(content)
    print(f"完了: {out_path}")
    print(f"  字幕 {len(cues)}行 / うち強調を付与 {emphasized}行")
    print(f"  焼き込み: ffmpeg -i 動画.mp4 -vf \"ass={os.path.basename(out_path)}\" -c:a copy 完成.mp4")
    print("  強調が的外れなら --keywords \"語1,語2\" で明示指定してください")

if __name__ == "__main__":
    main()
