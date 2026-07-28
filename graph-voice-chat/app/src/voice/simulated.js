// Simulated mode: replays the canonical demo with no API key. Assistant lines
// are spoken with the Web Speech API; graph payloads go through the exact
// same applyOperations path as live tool calls.

import { DEMO_STEPS } from '../data/demoScript.js'

export function playDemoStep(index, { applyOperations, setCaptions, setSpeaking }) {
  const step = DEMO_STEPS[index]
  if (!step) return false

  setCaptions({ user: step.user, assistant: '' })

  setTimeout(() => {
    applyOperations(step.payload)
    setCaptions({ assistant: step.assistant })
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(step.assistant)
      u.rate = 1.04
      u.onstart = () => setSpeaking(true)
      u.onend = () => setSpeaking(false)
      u.onerror = () => setSpeaking(false)
      window.speechSynthesis.speak(u)
    }
  }, 650)

  return true
}

export function stopSpeech() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}

export const DEMO_LENGTH = DEMO_STEPS.length
