import { useState, useRef, useCallback } from 'react';

/**
 * Handles canvas + audio export as WebM.
 * @param {object} params
 * @param {React.RefObject} params.canvasRef
 * @param {AudioContext} params.audioContext
 * @param {number} params.loopDuration - seconds for one full loop
 */
export function useExport({ canvasRef, audioContext, loopDuration }) {
  const [isExporting, setIsExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startExport = useCallback(async (onAudioSetup) => {
    if (!canvasRef.current || !audioContext || isExporting) return;

    setIsExporting(true);
    setProgress(0);
    chunksRef.current = [];

    // Create audio output for export
    const dest = audioContext.createMediaStreamDestination();
    onAudioSetup?.(dest); // caller connects audio to dest

    // Canvas stream
    const canvasStream = canvasRef.current.captureStream(30);

    // Merge canvas + audio tracks
    const combinedStream = new MediaStream([
      ...canvasStream.getVideoTracks(),
      ...dest.stream.getAudioTracks(),
    ]);

    const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')
      ? 'video/webm;codecs=vp9,opus'
      : MediaRecorder.isTypeSupported('video/webm')
      ? 'video/webm'
      : '';

    const recorder = new MediaRecorder(combinedStream, mimeType ? { mimeType } : {});
    recorderRef.current = recorder;

    recorder.ondataavailable = e => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'video/webm' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'clip-beat.webm';
      a.click();
      URL.revokeObjectURL(url);
      setIsExporting(false);
      setProgress(0);
      onAudioSetup?.(null); // disconnect
    };

    recorder.start(100); // collect data every 100ms

    // Progress updates
    const start = Date.now();
    const interval = setInterval(() => {
      const elapsed = (Date.now() - start) / 1000;
      setProgress(Math.min(elapsed / loopDuration, 1));
    }, 100);

    // Stop after one full loop
    setTimeout(() => {
      clearInterval(interval);
      if (recorder.state !== 'inactive') recorder.stop();
    }, loopDuration * 1000 + 200);
  }, [canvasRef, audioContext, loopDuration, isExporting]);

  const cancelExport = useCallback(() => {
    if (recorderRef.current?.state !== 'inactive') {
      recorderRef.current.stop();
    }
    setIsExporting(false);
    setProgress(0);
  }, []);

  return { isExporting, progress, startExport, cancelExport };
}
