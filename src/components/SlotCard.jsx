import { useRef, useEffect } from 'react';
import { SLOT_COLORS, SLOT_NAMES, SLOT_ICONS } from '../utils/midiMapping';

/**
 * SlotCard - individual pad for recording or playback.
 * mode: 'record' | 'playback'
 */
export function SlotCard({
  index,          // 1-5
  mode,           // 'record' | 'playback'
  stream,         // MediaStream for live camera preview
  objectUrl,      // recorded clip URL
  isRecording,    // bool - currently recording this slot
  isHit,          // bool - currently being triggered in playback
  onRecord,       // () => void
  videoRef,       // ref to the playback video element
}) {
  const previewRef = useRef(null);
  const color = SLOT_COLORS[index];
  const name = SLOT_NAMES[index];
  const icon = SLOT_ICONS[index];

  // Attach live camera stream to preview video
  useEffect(() => {
    if (previewRef.current && stream && !objectUrl && mode === 'record') {
      previewRef.current.srcObject = stream;
    }
  }, [stream, objectUrl, mode]);

  // In playback mode, attach objectUrl to the video element via ref
  useEffect(() => {
    if (videoRef?.current && objectUrl && mode === 'playback') {
      videoRef.current.src = objectUrl;
      videoRef.current.load();
    }
  }, [objectUrl, mode, videoRef]);

  const isEmpty = !objectUrl;

  return (
    <div
      className={`slot-card ${isHit ? 'slot-hit' : ''} ${isRecording ? 'slot-recording' : ''} ${isEmpty && mode === 'record' ? 'slot-empty' : ''}`}
      style={{ '--slot-color': color }}
    >
      {/* Slot header */}
      <div className="slot-header">
        <span className="slot-number">{String(index).padStart(2, '0')}</span>
        <span className="slot-icon">{icon}</span>
        <span className="slot-name">{name}</span>
      </div>

      {/* Video area */}
      <div className="slot-video-area" onClick={mode === 'record' ? onRecord : undefined}>
        {mode === 'record' ? (
          <>
            {/* Live preview or recorded clip */}
            <video
              ref={objectUrl ? undefined : previewRef}
              src={objectUrl || undefined}
              className="slot-video"
              autoPlay
              muted
              loop={!!objectUrl}
              playsInline
            />
            {/* Overlay label */}
            <div className={`slot-overlay ${isRecording ? 'recording' : ''}`}>
              {isRecording ? (
                <span className="rec-indicator">● REC</span>
              ) : objectUrl ? (
                <span className="rerecord-label">TAP TO RE-RECORD</span>
              ) : (
                <span className="tap-label">TAP TO RECORD</span>
              )}
            </div>
          </>
        ) : (
          /* Playback mode video */
          <video
            ref={videoRef}
            className="slot-video"
            muted
            playsInline
            preload="auto"
          />
        )}
      </div>

      {/* Bottom bar */}
      <div className="slot-footer">
        {isHit && <span className="hit-flash">▶ HIT</span>}
        {isRecording && <span className="countdown-bar" />}
      </div>
    </div>
  );
}
