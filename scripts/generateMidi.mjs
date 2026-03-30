/**
 * generateMidi.mjs
 * Generates beat_pattern.mid for Clip Beat app.
 * Run: node scripts/generateMidi.mjs
 *
 * Pattern: 100 BPM, 4/4, 4 bars (16 beats)
 * Note 36 (Kick)   → Slot 1: every 2 beats  [0,2,4,6,8,10,12,14]
 * Note 38 (Snare)  → Slot 2: off-beats      [1,3,5,7,9,11,13,15]
 * Note 42 (HiHat)  → Slot 3: every 0.5 beats
 * Note 45 (Tom)    → Slot 4: bar-end fills  [3.75,7.75,11.75,15.75]
 * Note 47 (Clap)   → Slot 5: every 4 beats  [1,5,9,13]
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const BPM = 100;
const TICKS_PER_BEAT = 480;
const TOTAL_BEATS = 16; // 4 bars of 4/4

// Beat positions for each note (in beats from start)
const PATTERN = [
  // Kick (36)
  ...[0, 2, 4, 6, 8, 10, 12, 14].map(b => ({ note: 36, beat: b, velocity: 110 })),
  // Snare (38)
  ...[1, 3, 5, 7, 9, 11, 13, 15].map(b => ({ note: 38, beat: b, velocity: 100 })),
  // HiHat (42) - every 0.5 beats
  ...Array.from({ length: 32 }, (_, i) => ({ note: 42, beat: i * 0.5, velocity: i % 2 === 0 ? 90 : 70 })),
  // Tom (45) - bar-end fills
  ...[3.75, 7.75, 11.75, 15.75].map(b => ({ note: 45, beat: b, velocity: 105 })),
  // Clap (47) - every 4 beats starting at 1
  ...[1, 5, 9, 13].map(b => ({ note: 47, beat: b, velocity: 95 })),
];

// Sort by beat time
PATTERN.sort((a, b) => a.beat - b.beat || a.note - b.note);

// Helper: encode variable-length quantity
function encodeVLQ(value) {
  const bytes = [];
  bytes.unshift(value & 0x7F);
  value >>= 7;
  while (value > 0) {
    bytes.unshift((value & 0x7F) | 0x80);
    value >>= 7;
  }
  return bytes;
}

// Helper: encode 4-byte big-endian int
function encode32(value) {
  return [(value >> 24) & 0xFF, (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF];
}

// Helper: encode 2-byte big-endian int
function encode16(value) {
  return [(value >> 8) & 0xFF, value & 0xFF];
}

// Build track events
const events = [];

// Tempo event: FF 51 03 [microseconds/beat]
const microsPerBeat = Math.round(60_000_000 / BPM); // 600000 for 100 BPM
events.push({
  tick: 0,
  data: [0xFF, 0x51, 0x03, (microsPerBeat >> 16) & 0xFF, (microsPerBeat >> 8) & 0xFF, microsPerBeat & 0xFF],
});

// Time signature: FF 58 04 04 02 18 08 (4/4)
events.push({
  tick: 0,
  data: [0xFF, 0x58, 0x04, 0x04, 0x02, 0x18, 0x08],
});

// Note events (Note On + Note Off pairs)
// Channel 9 (0-indexed, so 0x99 = channel 10 = drum channel)
const NOTE_ON = 0x99;
const NOTE_OFF = 0x89;
const NOTE_DURATION_TICKS = Math.round(TICKS_PER_BEAT * 0.1); // short note

for (const { note, beat, velocity } of PATTERN) {
  const tick = Math.round(beat * TICKS_PER_BEAT);
  events.push({ tick, data: [NOTE_ON, note, velocity] });
  events.push({ tick: tick + NOTE_DURATION_TICKS, data: [NOTE_OFF, note, 0] });
}

// End of track: FF 2F 00
const endTick = TOTAL_BEATS * TICKS_PER_BEAT;
events.push({ tick: endTick, data: [0xFF, 0x2F, 0x00] });

// Sort events by tick
events.sort((a, b) => a.tick - b.tick || (a.data[0] === 0xFF ? 1 : -1));

// Convert to delta-time events
const trackBytes = [];
let lastTick = 0;
for (const event of events) {
  const delta = event.tick - lastTick;
  lastTick = event.tick;
  trackBytes.push(...encodeVLQ(delta), ...event.data);
}

// Build MIDI file bytes
const header = [
  // MThd
  0x4D, 0x54, 0x68, 0x64,
  // Length = 6
  ...encode32(6),
  // Format 0
  ...encode16(0),
  // NumTracks = 1
  ...encode16(1),
  // Ticks per beat
  ...encode16(TICKS_PER_BEAT),
];

const track = [
  // MTrk
  0x4D, 0x54, 0x72, 0x6B,
  // Track length
  ...encode32(trackBytes.length),
  // Track data
  ...trackBytes,
];

const midiBytes = new Uint8Array([...header, ...track]);

const outPath = join(__dirname, '..', 'public', 'beat_pattern.mid');
mkdirSync(join(__dirname, '..', 'public'), { recursive: true });
writeFileSync(outPath, midiBytes);

console.log(`✓ Generated beat_pattern.mid (${midiBytes.length} bytes) → ${outPath}`);
console.log(`  BPM: ${BPM} | Bars: 4 | Ticks/beat: ${TICKS_PER_BEAT}`);
console.log(`  Notes: ${PATTERN.length} events`);
