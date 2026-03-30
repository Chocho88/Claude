import { useState, useEffect } from 'react';
import { NOTE_TO_SLOT } from '../utils/midiMapping';
import { DEFAULT_SCHEDULE } from '../utils/defaultSchedule';

/**
 * Loads and parses beat_pattern.mid into a usable schedule.
 * Falls back to DEFAULT_SCHEDULE if MIDI loading fails.
 */
export function useMidiParser() {
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const { Midi } = await import('@tonejs/midi');
        const basePath = import.meta.env.BASE_URL || '/';
        const midiUrl = `${basePath}beat_pattern.mid`.replace('//', '/');
        const midi = await Midi.fromUrl(midiUrl);

        if (cancelled) return;

        const bpm = midi.header.tempos[0]?.bpm ?? 100;
        const ticksPerBeat = midi.header.ppq;
        const totalBeats = 16;
        const loopDuration = (totalBeats * 60) / bpm;

        const slots = {};
        const track = midi.tracks[0];

        if (track) {
          for (const note of track.notes) {
            const slotIdx = NOTE_TO_SLOT[note.midi];
            if (slotIdx != null) {
              if (!slots[slotIdx]) slots[slotIdx] = [];
              slots[slotIdx].push(note.time); // time in seconds
            }
          }
        }

        // Fill any missing slots from DEFAULT_SCHEDULE
        for (let i = 1; i <= 5; i++) {
          if (!slots[i] || slots[i].length === 0) {
            slots[i] = DEFAULT_SCHEDULE.slots[i];
          }
        }

        setSchedule({ bpm, totalBeats, loopDuration, slots });
      } catch (err) {
        console.warn('MIDI parse failed, using default schedule:', err);
        if (!cancelled) {
          setError(err);
          setSchedule(DEFAULT_SCHEDULE);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  return { schedule, loading, error };
}
