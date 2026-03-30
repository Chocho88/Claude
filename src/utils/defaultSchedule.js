/**
 * Hardcoded fallback schedule matching beat_pattern.mid
 * Used if the MIDI file cannot be loaded/parsed.
 * Times are in seconds at 100 BPM (1 beat = 0.6s).
 */
const BEAT = 0.6; // seconds per beat at 100 BPM

function beatsToSeconds(beats) {
  return beats.map(b => b * BEAT);
}

export const DEFAULT_SCHEDULE = {
  bpm: 100,
  totalBeats: 16,
  loopDuration: 16 * BEAT,
  slots: {
    1: beatsToSeconds([0, 2, 4, 6, 8, 10, 12, 14]),
    2: beatsToSeconds([1, 3, 5, 7, 9, 11, 13, 15]),
    3: beatsToSeconds(Array.from({ length: 32 }, (_, i) => i * 0.5)),
    4: beatsToSeconds([3.75, 7.75, 11.75, 15.75]),
    5: beatsToSeconds([1, 5, 9, 13]),
  },
};
