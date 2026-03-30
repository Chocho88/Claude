import { useState, useRef, useCallback, useEffect } from 'react';
import * as Tone from 'tone';

/**
 * Manages Tone.js Transport + AudioBuffer playback.
 * @param {object} schedule - { bpm, totalBeats, loopDuration, slots }
 * @param {AudioBuffer[]} audioBuffers - keyed by slot index (1-5)
 * @param {AudioContext} audioContext
 * @param {function} onSlotHit - (slotIndex) => void
 */
export function useAudioEngine({ schedule, audioBuffers, audioContext, onSlotHit }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const scheduledIds = useRef([]);
  const onSlotHitRef = useRef(onSlotHit);

  useEffect(() => { onSlotHitRef.current = onSlotHit; }, [onSlotHit]);

  const stop = useCallback(() => {
    Tone.getTransport().stop();
    Tone.getTransport().cancel();
    scheduledIds.current = [];
    setIsPlaying(false);
  }, []);

  const start = useCallback(async () => {
    if (!schedule || !audioContext) return;

    // Must resume AudioContext on user gesture
    await Tone.start();
    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }

    const transport = Tone.getTransport();
    transport.stop();
    transport.cancel();
    transport.bpm.value = schedule.bpm;

    const loopEndBeats = schedule.totalBeats;
    transport.loop = true;
    transport.loopStart = 0;
    transport.loopEnd = `${loopEndBeats}i`; // in ticks? Use seconds instead
    transport.loopEnd = schedule.loopDuration;

    // Schedule all hits
    for (const [slotStr, times] of Object.entries(schedule.slots)) {
      const slot = Number(slotStr);
      const buffer = audioBuffers[slot];

      for (const time of times) {
        const id = transport.schedule((toneTime) => {
          // Play audio
          if (buffer && audioContext) {
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(toneTime);
          }
          // Trigger visual callback (Tone schedules on audio thread, use Tone.getDraw for RAF-sync)
          Tone.getDraw().schedule(() => {
            onSlotHitRef.current?.(slot);
          }, toneTime);
        }, time);
        scheduledIds.current.push(id);
      }
    }

    transport.start('+0.1');
    setIsPlaying(true);
  }, [schedule, audioBuffers, audioContext]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      Tone.getTransport().stop();
      Tone.getTransport().cancel();
    };
  }, []);

  return { isPlaying, start, stop };
}
