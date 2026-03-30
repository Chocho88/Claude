import { useState, useRef, useCallback, useEffect } from 'react';

const RECORD_DURATION_MS = 700;

function getSupportedMimeType() {
  const types = [
    'video/webm;codecs=vp9,opus',
    'video/webm;codecs=vp8,opus',
    'video/webm',
    'video/mp4',
  ];
  return types.find(t => MediaRecorder.isTypeSupported(t)) || '';
}

export function useCamera() {
  const [hasPermission, setHasPermission] = useState(false);
  const [permissionError, setPermissionError] = useState(null);
  const [stream, setStream] = useState(null);
  const [recordingSlot, setRecordingSlot] = useState(null);

  const streamRef = useRef(null);
  const objectUrlsRef = useRef({});

  const requestPermission = useCallback(async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: true,
      });
      streamRef.current = s;
      setStream(s);
      setHasPermission(true);
      setPermissionError(null);
      return s;
    } catch (err) {
      const msg =
        err.name === 'NotAllowedError'
          ? 'Camera and microphone access denied. Please allow access in your browser settings.'
          : err.name === 'NotFoundError'
          ? 'No camera or microphone found on this device.'
          : `Could not access camera: ${err.message}`;
      setPermissionError(msg);
      setHasPermission(false);
      return null;
    }
  }, []);

  const startRecording = useCallback(
    (slotIndex, onComplete) => {
      const s = streamRef.current;
      if (!s) return;

      setRecordingSlot(slotIndex);

      // Revoke previous object URL for this slot
      if (objectUrlsRef.current[slotIndex]) {
        URL.revokeObjectURL(objectUrlsRef.current[slotIndex]);
        delete objectUrlsRef.current[slotIndex];
      }

      const mimeType = getSupportedMimeType();
      const recorder = new MediaRecorder(s, mimeType ? { mimeType } : {});
      const chunks = [];

      recorder.ondataavailable = e => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: mimeType || 'video/webm' });
        const objectUrl = URL.createObjectURL(blob);
        objectUrlsRef.current[slotIndex] = objectUrl;
        setRecordingSlot(null);
        onComplete({ blob, objectUrl });
      };

      recorder.start();

      // Auto-stop after RECORD_DURATION_MS
      setTimeout(() => {
        if (recorder.state !== 'inactive') recorder.stop();
      }, RECORD_DURATION_MS);
    },
    []
  );

  // Stop all tracks when unmounting
  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach(t => t.stop());
      Object.values(objectUrlsRef.current).forEach(url => URL.revokeObjectURL(url));
    };
  }, []);

  return {
    stream,
    hasPermission,
    permissionError,
    recordingSlot,
    requestPermission,
    startRecording,
  };
}
