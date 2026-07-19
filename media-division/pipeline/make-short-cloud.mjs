// クラウド完結版パイプライン: edge-tts音声つきショートを1コマンドで生成
//
//   node make-short-cloud.mjs <scenario.json> [out.mp4]
//
// 前提（環境セットアップは pipeline/README.md 参照）:
//   apt ffmpeg / pip edge-tts（certifiにプロキシCA追加済み）/ playwright-core
//
// voicevox-local/make-short.mjs のクラウド版。TTSをVOICEVOXから
// edge-tts（ja-JP-KeitaNeural）に置き換えた以外は同じ流れ。
// テンプレートは voicevox-local/template.html を共用する。

import { execFileSync } from 'node:child_process';
import { readFileSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const [scenarioPath, outMp4 = 'out.mp4'] = process.argv.slice(2);
if (!scenarioPath) { console.error('usage: node make-short-cloud.mjs <scenario.json> [out.mp4]'); process.exit(1); }
const TRIM = 0.3, LEAD = 0.35, TAIL = 0.55, GAP = 0.15;

const sc = JSON.parse(readFileSync(scenarioPath, 'utf8'));
const voice = sc.voiceName ?? 'ja-JP-KeitaNeural';
const rate = sc.rate ?? '+8%';
const work = join(dirname(resolve(scenarioPath)), 'work');
mkdirSync(work, { recursive: true });

const dur = (f) => parseFloat(execFileSync('ffprobe',
  ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', f], { encoding: 'utf8' }));

console.log(`[1/3] 音声合成 (${voice}) ...`);
const segs = [];
let t = 0.6;
for (let i = 0; i < sc.scenes.length; i++) {
  const mp3 = join(work, `seg${i}.mp3`);
  execFileSync('edge-tts', ['--voice', voice, `--rate=${rate}`, '--text', sc.scenes[i].voice, '--write-media', mp3]);
  const d = dur(mp3);
  const start = t, voiceAt = start + LEAD, end = voiceAt + d + TAIL;
  segs.push({ mp3, start, voiceAt, end });
  console.log(`  scene ${i}: ${d.toFixed(2)}s 表示${start.toFixed(2)}〜${end.toFixed(2)}s`);
  t = end + GAP;
}
const total = t + 1.0;

console.log(`[2/3] 録画 (${total.toFixed(1)}s) ...`);
let chromium;
try { ({ chromium } = await import('playwright')); }
catch { ({ chromium } = await import('playwright-core')); }
const launchOpts = { args: ['--no-sandbox'] };
const pwDir = process.env.PLAYWRIGHT_BROWSERS_PATH;
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
await page.goto('file://' + resolve(HERE, 'voicevox-local', 'template.html'));
await page.waitForTimeout(total * 1000 + 400);
const webm = await page.video().path();
await ctx.close();
await browser.close();

console.log('[3/3] 合成 ...');
const inputs = segs.flatMap(({ mp3 }) => ['-i', mp3]);
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
console.log(`完成: ${outMp4} (${(total - TRIM).toFixed(1)}s)`);
