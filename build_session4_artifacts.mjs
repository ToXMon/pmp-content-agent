import fs from 'node:fs';

const capturePath = '/private/tmp/pmp-session4-capture.json';
const items = JSON.parse(fs.readFileSync(capturePath, 'utf8'))
  .map(([i, text]) => [Number(i), String(text)])
  .sort((a, b) => a[0] - b[0]);
const outDir = process.cwd();
const source = 'https://skillsoftbootcamp.zoom.us/rec/share/2dxi39e34LApXKKmOnx8X2FRe3g4-85s1RhtTgsXEwlpH_dQyRkK1TOuhfl5F1Fm.-LlIx6RtpemPzL_0';
const words = (s) => s.trim().split(/\s+/).filter(Boolean).length;
const esc = (s) => s.replace(/\r?\n/g, '\n');

const ids = items.map(([i]) => i);
const first = ids[0];
const last = ids.at(-1);
const unique = new Set(ids);
const gaps = [];
for (let i = first; i <= last; i++) if (!unique.has(i)) gaps.push(i);
if (unique.size !== items.length) throw new Error('Duplicate source entry IDs found');
if (first !== 0) throw new Error(`Expected source capture to begin at 0, found ${first}`);

const gapText = gaps.length
  ? `Zoom did not render source entr${gaps.length === 1 ? 'y' : 'ies'} ${gaps.join(', ')}; targeted rescans did not expose ${gaps.length === 1 ? 'it' : 'them'}. The transcript text for ${gaps.length === 1 ? 'this entry is' : 'these entries is'} unavailable, so no content is inferred. `
  : '';
const extractionStatus = gaps.length
  ? `Captured ${items.length} rendered transcript entries with source IDs ${first}–${last}; ${gaps.length} source ${gaps.length === 1 ? 'ID is' : 'IDs are'} unavailable. ${gapText}The entry IDs are retained for provenance and retrieval. Speaker names and timestamps are included where Zoom exposed them.`
  : `Complete Zoom automatic-transcript capture. Source entry IDs ${first}–${last} are present in order with no gaps. The entry IDs are retained for provenance and retrieval. Speaker names are included when Zoom exposed them; Zoom's transcript UI did not expose timestamps in the captured item text for every entry, so no timestamps are invented.`;

const transcript = `# November 2026 — PMP Bootcamp Session 4 transcript\n\n` +
`Source replay: ${source}\n\n` +
`Date shown by Zoom: November 19, 2026\n\n` +
`## Extraction status\n\n${extractionStatus}\n\n` +
`## Transcript\n\n` +
items.map(([i, text]) => `### Source entry ${i}\n\n${esc(text)}\n`).join('\n');
fs.writeFileSync(`${outDir}/November 2026 Session 4 transcript.md`, transcript);

const chunks = [];
let current = [];
let currentWords = 0;
for (const [i, text] of items) {
  const n = words(text);
  const hasGap = current.length && i !== current.at(-1)[0] + 1;
  if (current.length && (hasGap || currentWords + n > 450)) {
    chunks.push(current);
    current = [];
    currentWords = 0;
  }
  current.push([i, text]);
  currentWords += n;
}
if (current.length) chunks.push(current);
const rag = `# November 2026 PMP Bootcamp — Session 4 RAG chunks\n\n` +
`Source: ${source}\n\n` +
`Chunking: contiguous Zoom source entries, approximately 450 words maximum per chunk. ` +
`Chunks split at missing source IDs. Use source entry IDs for citation and deduplication. ` +
`This file preserves transcript text; it is not a summary. ${gaps.length ? `Source IDs not rendered by Zoom: ${gaps.join(', ')}.` : ''}\n\n` +
chunks.map((chunk, idx) => {
  const start = chunk[0][0];
  const end = chunk[chunk.length - 1][0];
  return `## Chunk ${String(idx + 1).padStart(4, '0')} — source entries ${start}–${end}\n\n` +
    chunk.map(([i, text]) => `**Source entry ${i}**\n\n${esc(text)}\n`).join('\n');
}).join('\n');
fs.writeFileSync(`${outDir}/November 2026 Session 4 - RAG chunks.md`, rag);

const byId = new Map(items);
const calloutRe = /exam|test|slide|important|remember|key\s+|susanism|call.?out|know this|must know|pay attention|tip|trick|formula|mindset|scope is king|you need to know|on the exam/i;
const calloutIds = items.filter(([, text]) => calloutRe.test(text)).map(([i]) => i);
let callouts = `# November 2026 PMP Bootcamp — Session 4 exam callouts and Susanisms\n\n` +
`Source: ${source}\n\n` +
`This file preserves transcript entries where Susan explicitly references exam/test content, slides, key points, memory aids, formulas, or Susanisms. ` +
`These are instructor guidance, not a guarantee of any particular PMI exam question. Every item retains its source-entry ID. ${gaps.length ? `Source IDs ${gaps.join(' and ')} were not rendered by Zoom.` : ''}\n\n`;
for (const id of calloutIds) callouts += `## Source entry ${id}\n\n${byId.get(id)}\n\n`;
callouts += `## Retrieval notes\n\n` +
`- Prioritize entries containing explicit phrases such as “on the exam,” “key study slide,” “you need to know,” or equivalent.\n` +
`- “Susanism” is preserved as Susan's own label for practical guidance; it is not PMI terminology.\n` +
`- Use the full transcript and RAG chunks for surrounding context, including the slide topic immediately before or after each callout.\n` +
(gaps.length ? `- Zoom did not render source entries ${gaps.join(' or ')}; their text is not included or inferred.\n` : '');
fs.writeFileSync(`${outDir}/November 2026 Session 4 - Exam callouts.md`, callouts);

console.log(JSON.stringify({ entries: items.length, first, last, gaps, chunks: chunks.length, callouts: calloutIds.length }));
