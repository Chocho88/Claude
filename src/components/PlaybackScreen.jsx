import { useRef, useEffect, useCallback, useState } from 'react';
import { SlotCard } from './SlotCard';
import { Timeline } from './Timeline';
import { ExportButton } from './ExportButton';
import { useAudioEngine } from '../hooks/useAudioEngine';
import { useExport } from '../hooks/useExport';

export function PlaybackScreen({ slots, schedule, audioContext, onBack }) {
  const [hitSlots, setHitSlots] = useState({});
  const canvasRef = useRef(null);
  // One stable ref-object per slot (1-indexed); React fills .current when <video> mounts
  const videoRefs = useRef(
    Object.fromEntries([1, 2, 3, 4, 5].map(i => [i, { current: null }]))
  );

  const handleSlotHit = useCallback((slotIndex) => {
    // Trigger video playback
    const vRef = videoRefs.current[slotIndex];
    if (vRef?.current) {
      vRef.current.currentTime = 0;
      vRef.current.play().catch(() => {});
    }

    // Visual pulse
    setHitSlots(prev => ({ ...prev, [slotIndex]: true }));
    setTimeout(() => {
      setHitSlots(prev => {
        const next = { ...prev };
        delete next[slotIndex];
        return next;
      });
    }, 300);
  }, []);

  const audioBuffers = {};
  slots.forEach((s, i) => {
    if (s?.audioBuffer) audioBuffers[i + 1] = s.audioBuffer;
  });

  const { isPlaying, start, stop } = useAudioEngine({
    schedule,
    audioBuffers,
    audioContext,
    onSlotHit: handleSlotHit,
  });

  const { isExporting, progress, startExport, cancelExport } = useExport({
    canvasRef,
    audioContext,
    loopDuration: schedule?.loopDuration ?? 9.6,
  });

  // Auto-start on mount
  useEffect(() => {
    if (schedule) start();
    return () => stop();
  }, [schedule]);

  const handlePlayPause = () => {
    if (isPlaying) stop();
    else start();
  };

  const handleExport = () => {
    startExport((dest) => {
      // When dest is provided, route audio to it as well
      // This is a simplified export - in full implementation
      // audio sources would connect to both destination and dest
    });
  };

  return (
    <div className="playback-screen">
      {/* Top bar */}
      <header className="playback-header">
        <button className="btn-back" onClick={() => { stop(); onBack(); }}>
          ← REC
        </button>
        <div className="logo-block small">
          <span className="logo-text">CLIP</span>
          <span className="logo-beat">BEAT</span>
        </div>
        <div className="bpm-display">
          <span className="bpm-label">BPM</span>
          <span className="bpm-value">{schedule?.bpm ?? 100}</span>
        </div>
      </header>

      {/* Slot grid - MPC layout */}
      <div className="slots-grid playback-grid">
        {slots.map((slot, i) => {
          const idx = i + 1;
          return (
            <SlotCard
              key={idx}
              index={idx}
              mode="playback"
              objectUrl={slot?.objectUrl}
              isHit={!!hitSlots[idx]}
              isRecording={false}
              videoRef={videoRefs.current[idx]}
            />
          );
        })}
      </div>

      {/* Controls */}
      <div className="playback-controls">
        <button
          className={`btn-play-pause ${isPlaying ? 'playing' : ''}`}
          onClick={handlePlayPause}
        >
          {isPlaying ? '⏸ PAUSE' : '▶ PLAY'}
        </button>
        <div className="loop-indicator">
          {isPlaying && <span className="loop-dot">●</span>}
          <span>LOOP</span>
        </div>
        <ExportButton
          isExporting={isExporting}
          progress={progress}
          onExport={handleExport}
          onCancel={cancelExport}
        />
      </div>

      {/* Timeline */}
      <Timeline
        isPlaying={isPlaying}
        totalBeats={schedule?.totalBeats ?? 16}
        schedule={schedule}
      />

      {/* Hidden canvas for export */}
      <canvas ref={canvasRef} width={1280} height={720} style={{ display: 'none' }} />
    </div>
  );
}
