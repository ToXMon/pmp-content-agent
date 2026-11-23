import fs from 'node:fs';

const capturePath = '/private/tmp/pmp-session2-capture.json';
const items = JSON.parse(fs.readFileSync(capturePath, 'utf8')).sort((a, b) => a[0] - b[0]);
const outDir = process.cwd();
const source = 'https://skillsoftbootcamp.zoom.us/rec/share/zc9dPIDLIBh52fEPiPEG5KlFzge2NFW57aCiwrjaC1GqIVWypL_wXg1l7JnI0f60.FXkzZvDtg7ZoNzTB';
const words = (s) => s.trim().split(/\s+/).filter(Boolean).length;
const esc = (s) => s.replace(/\r?\n/g, '\n');

const transcript = `# November 2026 — PMP Bootcamp Session 2 transcript\n\n` +
`Source replay: ${source}\n\n` +
`Date shown by Zoom: November 17, 2026\n\n` +
`## Extraction status\n\n` +
`Complete Zoom automatic-transcript capture. Source entry IDs 0–2188 are present in order with no gaps. ` +
`The entry IDs are retained for provenance and retrieval. Speaker names are included when Zoom exposed them; ` +
`Zoom's transcript UI did not expose timestamps in the captured item text for every entry, so no timestamps are invented.\n\n` +
`## Transcript\n\n` +
items.map(([i, text]) => `### Source entry ${i}\n\n${esc(text)}\n`).join('\n');
fs.writeFileSync(`${outDir}/November 2026 Session 2 transcript.md`, transcript);

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
const rag = `# November 2026 PMP Bootcamp — Session 2 RAG chunks\n\n` +
`Source: ${source}\n\n` +
`Chunking: contiguous Zoom source entries, approximately 450 words maximum per chunk. ` +
`Use source entry IDs for citation and deduplication. This file preserves the transcript text; it is not a summary.\n\n` +
chunks.map((chunk, idx) => {
  const start = chunk[0][0];
  const end = chunk[chunk.length - 1][0];
  return `## Chunk ${String(idx + 1).padStart(4, '0')} — source entries ${start}–${end}\n\n` +
    chunk.map(([i, text]) => `**Source entry ${i}**\n\n${esc(text)}\n`).join('\n');
}).join('\n');
fs.writeFileSync(`${outDir}/November 2026 Session 2 - RAG chunks.md`, rag);

const byId = new Map(items);
const selected = {
  'Explicit key-study-slide callouts': [163, 164, 165, 166, 864, 865, 962, 1255, 1256, 1367, 1963],
  'Explicit exam-content callouts': [101, 238, 601, 755, 827, 828, 837, 886, 888, 1059, 1060, 1220, 1316, 1372, 1373, 1374, 1375, 1376, 1614, 2132, 2161, 2162],
  'Susanisms and memorable guidance': [8, 105, 193, 226, 238, 329, 372, 493, 717, 862, 882, 990, 1337, 1354, 1365, 1639, 1669, 1746, 1946],
  'Study-resource and deck references': [29, 30, 457, 459, 769, 1810, 1811, 2118]
};
let callouts = `# November 2026 PMP Bootcamp — Session 2 exam callouts and Susanisms\n\n` +
`Source: ${source}\n\n` +
`These are Susan Daniels' explicit study/exam callouts and memorable guidance as captured in the Zoom transcript. ` +
`They are instructor guidance, not a guarantee of any particular PMI exam question. Every item retains its source-entry ID.\n\n`;
for (const [heading, ids] of Object.entries(selected)) {
  callouts += `## ${heading}\n\n`;
  for (const id of ids) {
    if (!byId.has(id)) continue;
    callouts += `### Source entry ${id}\n\n${byId.get(id)}\n\n`;
  }
}
callouts += `## Retrieval notes\n\n` +
`- Highest-confidence exam-study instructions are the entries where Susan explicitly says “key study slide,” “on the exam,” “you need to know,” or equivalent.\n` +
`- “Susanism” is preserved as Susan's own label for practical guidance; it is not PMI terminology.\n` +
`- Use the full transcript and RAG chunks for surrounding context, including the slide topic immediately before or after a callout.\n`;
fs.writeFileSync(`${outDir}/November 2026 Session 2 - Exam callouts.md`, callouts);

console.log(JSON.stringify({ entries: items.length, first: items[0][0], last: items.at(-1)[0], chunks: chunks.length }));
