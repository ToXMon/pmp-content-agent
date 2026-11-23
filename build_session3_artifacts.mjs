import fs from 'node:fs';

const capturePath = '/private/tmp/pmp-session3-capture.json';
const items = JSON.parse(fs.readFileSync(capturePath, 'utf8')).sort((a, b) => a[0] - b[0]);
const outDir = process.cwd();
const source = 'https://skillsoftbootcamp.zoom.us/rec/share/_V9xeFncyI5fkdCc7a_qVLcyaWrlLFaoB3lYVcT3UzCWB1tTA85RRYztiU7m1z4n.fUTiwEaQ9yPnP2eH';
const words = (s) => s.trim().split(/\s+/).filter(Boolean).length;
const esc = (s) => s.replace(/\r?\n/g, '\n');

const transcript = `# November 2026 — PMP Bootcamp Session 3 transcript\n\n` +
`Source replay: ${source}\n\n` +
`Date shown by Zoom: November 18, 2026\n\n` +
`## Extraction status\n\n` +
`Complete Zoom automatic-transcript capture. Source entry IDs 0–${items.at(-1)[0]} are present in order with no gaps. ` +
`The entry IDs are retained for provenance and retrieval. Speaker names are included when Zoom exposed them; ` +
`Zoom's transcript UI did not expose timestamps in the captured item text for every entry, so no timestamps are invented.\n\n` +
`## Transcript\n\n` +
items.map(([i, text]) => `### Source entry ${i}\n\n${esc(text)}\n`).join('\n');
fs.writeFileSync(`${outDir}/November 2026 Session 3 transcript.md`, transcript);

const chunks = [];
let current = [];
let currentWords = 0;
for (const [i, text] of items) {
  const n = words(text);
  if (current.length && currentWords + n > 450) {
    chunks.push(current);
    current = [];
    currentWords = 0;
  }
  current.push([i, text]);
  currentWords += n;
}
if (current.length) chunks.push(current);
const rag = `# November 2026 PMP Bootcamp — Session 3 RAG chunks\n\n` +
`Source: ${source}\n\n` +
`Chunking: contiguous Zoom source entries, approximately 450 words maximum per chunk. ` +
`Use source entry IDs for citation and deduplication. This file preserves transcript text; it is not a summary.\n\n` +
chunks.map((chunk, idx) => {
  const start = chunk[0][0];
  const end = chunk[chunk.length - 1][0];
  return `## Chunk ${String(idx + 1).padStart(4, '0')} — source entries ${start}–${end}\n\n` +
    chunk.map(([i, text]) => `**Source entry ${i}**\n\n${esc(text)}\n`).join('\n');
}).join('\n');
fs.writeFileSync(`${outDir}/November 2026 Session 3 - RAG chunks.md`, rag);

const byId = new Map(items);
const calloutRe = /exam|test|slide|important|remember|key\s+|susanism|call.?out|know this|must know|pay attention|tip|trick|formula|mindset|scope is king|you need to know|on the exam/i;
const calloutIds = items.filter(([, text]) => calloutRe.test(text)).map(([i]) => i);
let callouts = `# November 2026 PMP Bootcamp — Session 3 exam callouts and Susanisms\n\n` +
`Source: ${source}\n\n` +
`This file preserves transcript entries where Susan explicitly references exam/test content, slides, key points, memory aids, formulas, or Susanisms. ` +
`These are instructor guidance, not a guarantee of any particular PMI exam question. Every item retains its source-entry ID.\n\n`;
for (const id of calloutIds) callouts += `## Source entry ${id}\n\n${byId.get(id)}\n\n`;
callouts += `## Retrieval notes\n\n` +
`- Prioritize entries containing explicit phrases such as “on the exam,” “key study slide,” “you need to know,” or equivalent.\n` +
`- “Susanism” is preserved as Susan's own label for practical guidance; it is not PMI terminology.\n` +
`- Use the full transcript and RAG chunks for surrounding context, including the slide topic immediately before or after each callout.\n`;
fs.writeFileSync(`${outDir}/November 2026 Session 3 - Exam callouts.md`, callouts);

console.log(JSON.stringify({ entries: items.length, first: items[0][0], last: items.at(-1)[0], chunks: chunks.length, callouts: calloutIds.length }));
