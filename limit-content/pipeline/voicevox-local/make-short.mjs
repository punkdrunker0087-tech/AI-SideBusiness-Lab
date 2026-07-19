// 分業パイプライン: VOICEVOX音声つきショートを1コマンドで生成（人間のPCで実行）
//
//   node make-short.mjs [scenario.json] [out.mp4]
//
// 前提: VOICEVOX起動中（127.0.0.1:50021）、ffmpegがPATHにあること、
//       npm i playwright && npx playwright install chromium 済みであること
//
// 流れ: シーンごとにTTS → wavの実測秒数からタイムラインを自動計算 →
//       template.htmlに注入してChromiumで録画 → ffmpegで音声を合成しmp4化

import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const [scenarioPath = join(HERE, 'scenario.json'), outMp4 = 'out.mp4'] = process.argv.slice(2);
const VV = process.env.VOICEVOX_URL ?? 'http://127.0.0.1:50021';
const TRIM = 0.3;          // 録画冒頭の読み込みフラッシュを切る秒数
const LEAD = 0.35;         // シーン表示から音声開始までの間
const TAIL = 0.55;         // 音声終了からシーン退場までの間
const GAP = 0.15;          // シーン間の間

const sc = JSON.parse(readFileSync(scenarioPath, 'utf8'));
const work = join(HERE, 'work');
mkdirSync(work, { recursive: true });

function wavDuration(buf) {
  const byteRate = buf.readUInt32LE(28);
  let off = 12;
  while (off + 8 <= buf.length) {
    const id = buf.toString('ascii', off, off + 4);
    const size = buf.readUInt32LE(off + 4);
    if (id === 'data') return size / byteRate;
    off += 8 + size + (size % 2);
  }
  throw new Error('WAV data chunk not found');
}

// ① シーンごとに音声合成し、実測秒数でタイムラインを組む
console.log(`[1/3] 音声合成 (speaker=${sc.speaker}) ...`);
const segs = [];
let t = 0.6; // 最初のシーンの開始時刻
for (let i = 0; i < sc.scenes.length; i++) {
  const text = sc.scenes[i].voice;
  const q = await fetch(`${VV}/audio_query?speaker=${sc.speaker}&text=${encodeURIComponent(text)}`, { method: 'POST' });
  if (!q.ok) throw new Error(`audio_query失敗 (scene ${i}): ${q.status}`);
  const s = await fetch(`${VV}/synthesis?speaker=${sc.speaker}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(await q.json()),
  });
  if (!s.ok) throw new Error(`synthesis失敗 (scene ${i}): ${s.status}`);
  const buf = Buffer.from(await s.arrayBuffer());
  const wav = join(work, `seg${i}.wav`);
  writeFileSync(wav, buf);
  const dur = wavDuration(buf);
  const start = t;                    // シーン表示開始
  const voiceAt = start + LEAD;       // 音声開始
  const end = voiceAt + dur + TAIL;   // シーン退場
  segs.push({ wav, dur, start, voiceAt, end });
  console.log(`  scene ${i}: ${dur.toFixed(2)}s 表示${start.toFixed(2)}〜${end.toFixed(2)}s`);
  t = end + GAP;
}
const total = t + 1.0;

// ② タイムラインを注入して録画
console.log(`[2/3] 録画 (${total.toFixed(1)}s) ...`);
let chromium;
try { ({ chromium } = await import('playwright')); }
catch { ({ chromium } = await import('playwright-core')); }
const launchOpts = { args: ['--no-sandbox'] };
const pwDir = process.env.PLAYWRIGHT_BROWSERS_PATH;   // クラウド環境用フォールバック
if (pwDir) {
  const hit = readdirSync(pwDir).find((d) => /^chromium-\d+$/.test(d));
  if (hit) launchOpts.executablePath = join(pwDir, hit, 'chrome-linux', 'chrome');
}
const browser = await chromium.launch(launchOpts);
const ctx = await browser.newContext({
  viewport: { width: 1080, height: 1920 },
  recordVideo: { dir: work, size: { width: 1080, height: 1920 } },
});
const page = await ctx.newPage();
await page.addInitScript(`window.SCENARIO=${JSON.stringify(sc)};window.TIMELINE=${JSON.stringify(segs.map(({ start, end }) => ({ start, end })))};`);
await page.goto('file://' + resolve(HERE, 'template.html'));
await page.waitForTimeout(total * 1000 + 400);
const webm = await page.video().path();
await ctx.close();
await browser.close();

// ③ 音声を各開始時刻に配置してmp4に合成
console.log('[3/3] 合成 ...');
const inputs = segs.flatMap(({ wav }) => ['-i', wav]);
const delays = segs.map(({ voiceAt }, i) => {
  const ms = Math.round((voiceAt - TRIM) * 1000);
  return `[${i + 1}:a]adelay=${ms}|${ms}[a${i}]`;
});
const mix = segs.map((_, i) => `[a${i}]`).join('') + `amix=inputs=${segs.length}:normalize=0[mix]`;
execFileSync('ffmpeg', [
  '-y', '-ss', String(TRIM), '-i', webm, ...inputs,
  '-filter_complex', [...delays, mix].join(';'),
  '-map', '0:v', '-map', '[mix]', '-t', String(total - TRIM),
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30', '-crf', '20',
  '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', outMp4,
], { stdio: 'inherit' });
console.log(`完成: ${outMp4} (${(total - TRIM).toFixed(1)}s) — クレジット表記: ${sc.credit}`);
