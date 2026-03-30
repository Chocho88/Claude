import { useRef, useEffect } from 'react';
import * as Tone from 'tone';

export function Timeline({ isPlaying, totalBeats = 16, schedule }) {
  const rafRef = useRef(null);
  const progressRef = useRef(null);
  const ticksRef = useRef([]);

  useEffect(() => {
    if (!isPlaying) {
      if (progressRef.current) {
        progressRef.current.style.width = '0%';
      }
      return;
    }

    function tick() {
      const transport = Tone.getTransport();
      const progress = transport.progress; // 0 to 1
      if (progressRef.current) {
        progressRef.current.style.width = `${progress * 100}%`;
      }

      // Highlight active beat tick marks
      const currentBeat = Math.floor(progress * totalBeats);
      ticksRef.current.forEach((el, i) => {
        if (!el) return;
        el.classList.toggle('tick-active', i === currentBeat);
      });

      rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [isPlaying, totalBeats]);

  return (
    <div className="timeline">
      <div className="timeline-label">LOOP</div>
      <div className="timeline-track">
        {/* Beat tick marks */}
        <div className="timeline-ticks">
          {Array.from({ length: totalBeats }, (_, i) => (
            <div
              key={i}
              className={`timeline-tick ${i % 4 === 0 ? 'tick-bar' : ''}`}
              ref={el => { ticksRef.current[i] = el; }}
            />
          ))}
        </div>
        {/* Progress bar */}
        <div className="timeline-progress-track">
          <div className="timeline-progress" ref={progressRef} />
        </div>
      </div>
      <div className="timeline-label">4 BARS</div>
    </div>
  );
}
