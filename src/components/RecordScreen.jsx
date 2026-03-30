import { useEffect, useRef } from 'react';
import { SlotCard } from './SlotCard';
import { SLOT_COLORS } from '../utils/midiMapping';

export function RecordScreen({ slots, stream, hasPermission, permissionError, recordingSlot, onRecord, onMakeBeat, onRequestPermission }) {
  const allFilled = slots.every(s => s?.objectUrl);

  return (
    <div className="record-screen">
      {/* Header */}
      <header className="app-header">
        <div className="logo-block">
          <span className="logo-text">CLIP</span>
          <span className="logo-beat">BEAT</span>
        </div>
        <div className="header-tag">VIDEO BEAT MAKER</div>
      </header>

      {/* Permission prompt */}
      {!hasPermission && (
        <div className="permission-panel">
          {permissionError ? (
            <div className="permission-error">
              <span className="error-icon">⚠</span>
              <p>{permissionError}</p>
              <button className="btn-primary" onClick={onRequestPermission}>
                TRY AGAIN
              </button>
            </div>
          ) : (
            <div className="permission-prompt">
              <p className="permission-label">CAMERA ACCESS REQUIRED</p>
              <p className="permission-sub">Record 5 clips to build your beat</p>
              <button className="btn-primary" onClick={onRequestPermission}>
                ENABLE CAMERA + MIC
              </button>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      {hasPermission && (
        <div className="instructions">
          <span className="inst-text">TAP EACH PAD — RECORD A 0.7s CLIP — BUILD YOUR BEAT</span>
          <span className="inst-count">{slots.filter(s => s?.objectUrl).length}/5 RECORDED</span>
        </div>
      )}

      {/* Slot grid */}
      <div className="slots-grid record-grid">
        {slots.map((slot, i) => (
          <SlotCard
            key={i + 1}
            index={i + 1}
            mode="record"
            stream={stream}
            objectUrl={slot?.objectUrl}
            isRecording={recordingSlot === i + 1}
            isHit={false}
            onRecord={() => hasPermission && onRecord(i + 1)}
          />
        ))}
      </div>

      {/* Make Beat button */}
      {allFilled && (
        <div className="make-beat-container">
          <button className="btn-make-beat" onClick={onMakeBeat}>
            <span>MAKE BEAT</span>
            <span className="btn-arrow">→</span>
          </button>
        </div>
      )}
    </div>
  );
}
