import { useEffect, useRef, useState } from 'react'
import { useGraphStore } from '../store/graphStore.js'
import { connectRealtime } from './realtime.js'
import { playDemoStep, stopSpeech, DEMO_LENGTH } from './simulated.js'

function Waveform({ active }) {
  return (
    <div className={`waveform ${active ? 'active' : ''}`}>
      {Array.from({ length: 24 }, (_, i) => (
        <span key={i} style={{ animationDelay: `${(i % 7) * 0.11}s` }} />
      ))}
    </div>
  )
}

export default function VoiceBar() {
  const { mode, captions, speaking, applyOperations, setCaptions, setSpeaking, reset } = useGraphStore()
  const [demoStep, setDemoStep] = useState(0)
  const [live, setLive] = useState('off') // off | connecting | on
  const [error, setError] = useState('')
  const sessionRef = useRef(null)

  const advanceDemo = () => {
    if (demoStep >= DEMO_LENGTH) {
      stopSpeech()
      reset()
      setDemoStep(0)
      return
    }
    playDemoStep(demoStep, { applyOperations, setCaptions, setSpeaking })
    setDemoStep((s) => s + 1)
  }

  useEffect(() => {
    if (mode !== 'simulated') return
    const onKey = (e) => {
      if (e.code === 'Space' && !e.target.closest('input,textarea,button')) {
        e.preventDefault()
        advanceDemo()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  // leaving live mode tears the session down
  useEffect(() => {
    if (mode !== 'live' && sessionRef.current) {
      sessionRef.current.disconnect()
      sessionRef.current = null
      setLive('off')
    }
    if (mode !== 'simulated') stopSpeech()
  }, [mode])

  const toggleMic = async () => {
    setError('')
    if (sessionRef.current) {
      sessionRef.current.disconnect()
      sessionRef.current = null
      setLive('off')
      setSpeaking(false)
      return
    }
    setLive('connecting')
    try {
      sessionRef.current = await connectRealtime({
        onToolCall: (payload) => applyOperations(payload),
        onUserCaption: (t) => setCaptions({ user: t }),
        onAssistantCaption: (t) => setCaptions({ assistant: t }),
        onSpeaking: (s) => setSpeaking(s),
        onError: (m) => setError(m),
      })
      setLive('on')
    } catch (err) {
      setLive('off')
      setError(`${err.message} — no key? Switch to Simulated mode.`)
    }
  }

  return (
    <div className="voicebar">
      {mode === 'live' ? (
        <button
          className={`mic mic-${live}`}
          onClick={toggleMic}
          title={live === 'on' ? 'Disconnect' : 'Connect live voice'}
        >
          {live === 'connecting' ? '…' : live === 'on' ? '■' : '🎤'}
        </button>
      ) : (
        <button className="mic mic-demo" onClick={advanceDemo}>
          {demoStep >= DEMO_LENGTH ? '↺' : '▶'}
        </button>
      )}
      <Waveform active={speaking || live === 'connecting'} />
      <div className="captions">
        {captions.user && <div className="caption-user">“{captions.user}”</div>}
        {captions.assistant && <div className="caption-assistant">{captions.assistant}</div>}
        {!captions.user && !captions.assistant && (
          <div className="caption-hint">
            {mode === 'simulated'
              ? `Press ▶ or Space to play the demo (${demoStep}/${DEMO_LENGTH})`
              : 'Tap the mic, then ask for restaurant recommendations in New York'}
          </div>
        )}
        {error && <div className="caption-error">{error}</div>}
      </div>
      {mode === 'simulated' && demoStep > 0 && (
        <div className="demo-progress">{Math.min(demoStep, DEMO_LENGTH)}/{DEMO_LENGTH}</div>
      )}
    </div>
  )
}
