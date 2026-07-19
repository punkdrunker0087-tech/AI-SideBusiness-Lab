// VOICEVOXローカル音声合成スクリプト（人間のPCで実行する）
// 前提: VOICEVOXアプリ（またはエンジン）が起動中で 127.0.0.1:50021 で待機していること
//
// 使い方:
//   node voicevox.mjs "読み上げるテキスト" out.wav [speakerId]
//   speakerId省略時は 3（ずんだもん・ノーマル）
//   話者一覧: curl http://127.0.0.1:50021/speakers
//
// クレジット表記を忘れない（例: 「VOICEVOX:ずんだもん」）

import { writeFileSync } from 'node:fs';

const [text, outPath = 'voice.wav', speaker = '3'] = process.argv.slice(2);
if (!text) {
  console.error('usage: node voicevox.mjs "テキスト" out.wav [speakerId]');
  process.exit(1);
}

const base = process.env.VOICEVOX_URL ?? 'http://127.0.0.1:50021';

const q = await fetch(`${base}/audio_query?speaker=${speaker}&text=${encodeURIComponent(text)}`, { method: 'POST' });
if (!q.ok) throw new Error(`audio_query failed: ${q.status} ${await q.text()}`);
const query = await q.json();

const s = await fetch(`${base}/synthesis?speaker=${speaker}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(query),
});
if (!s.ok) throw new Error(`synthesis failed: ${s.status} ${await s.text()}`);

writeFileSync(outPath, Buffer.from(await s.arrayBuffer()));
console.log(`OK: ${outPath} (speaker=${speaker}, ${text.length}文字)`);
