/**
 * Extracts a decoded AudioBuffer from a video/audio Blob.
 * @param {Blob} blob - The recorded video blob
 * @param {AudioContext} audioContext
 * @returns {Promise<AudioBuffer>}
 */
export async function extractAudioBuffer(blob, audioContext) {
  const arrayBuffer = await blob.arrayBuffer();
  try {
    return await audioContext.decodeAudioData(arrayBuffer);
  } catch (err) {
    console.warn('Failed to decode audio data:', err);
    // Return a silent 0.7s buffer as fallback
    const sampleRate = audioContext.sampleRate;
    const frameCount = Math.ceil(sampleRate * 0.7);
    return audioContext.createBuffer(1, frameCount, sampleRate);
  }
}
