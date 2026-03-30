import { useState, useRef, useCallback } from 'react';
import { RecordScreen } from './components/RecordScreen';
import { PlaybackScreen } from './components/PlaybackScreen';
import { useCamera } from './hooks/useCamera';
import { useMidiParser } from './hooks/useMidiParser';
import { extractAudioBuffer } from './utils/audioExtractor';
import './App.css';

const SLOT_COUNT = 5;
const emptySlots = () => Array(SLOT_COUNT).fill(null);

export default function App() {
  const [screen, setScreen] = useState('record');
  const [slots, setSlots] = useState(emptySlots());
  const [loadingMessage, setLoadingMessage] = useState('');
  const audioContextRef = useRef(null);

  const { schedule } = useMidiParser();

  const {
    stream,
    hasPermission,
    permissionError,
    recordingSlot,
    requestPermission,
    startRecording,
  } = useCamera();

  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContextRef.current;
  }, []);

  const handleRequestPermission = useCallback(async () => {
    getAudioContext();
    await requestPermission();
  }, [requestPermission, getAudioContext]);

  const handleRecord = useCallback((slotIndex) => {
    getAudioContext();
    startRecording(slotIndex, ({ blob, objectUrl }) => {
      setSlots(prev => {
        const next = [...prev];
        next[slotIndex - 1] = { blob, objectUrl, audioBuffer: null };
        return next;
      });
    });
  }, [startRecording, getAudioContext]);

  const handleMakeBeat = useCallback(async () => {
    const ac = getAudioContext();
    setScreen('loading');
    setLoadingMessage('DECODING AUDIO…');
    try {
      const decoded = await Promise.all(
        slots.map(async (slot) => {
          if (!slot?.blob) return null;
          const audioBuffer = await extractAudioBuffer(slot.blob, ac);
          return { ...slot, audioBuffer };
        })
      );
      setSlots(decoded);
      setLoadingMessage('');
      setScreen('playback');
    } catch (err) {
      console.error('Audio decode failed:', err);
      setLoadingMessage('');
      setScreen('record');
    }
  }, [slots, getAudioContext]);

  const handleBack = useCallback(() => {
    setScreen('record');
  }, []);

  if (screen === 'loading') {
    return (
      <div className="loading-screen">
        <div className="loading-inner">
          <div className="loading-spinner" />
          <p className="loading-text">{loadingMessage}</p>
        </div>
      </div>
    );
  }

  if (screen === 'record') {
    return (
      <RecordScreen
        slots={slots}
        stream={stream}
        hasPermission={hasPermission}
        permissionError={permissionError}
        recordingSlot={recordingSlot}
        onRecord={handleRecord}
        onMakeBeat={handleMakeBeat}
        onRequestPermission={handleRequestPermission}
      />
    );
  }

  return (
    <PlaybackScreen
      slots={slots}
      schedule={schedule}
      audioContext={audioContextRef.current}
      onBack={handleBack}
    />
  );
}
