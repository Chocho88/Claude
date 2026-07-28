// Live voice: WebRTC session against the OpenAI Realtime API (the native
// ChatGPT voice stack). The API key stays on the token server; the browser
// only ever sees a short-lived client secret from POST /session.

export async function connectRealtime({ onToolCall, onUserCaption, onAssistantCaption, onSpeaking, onError }) {
  const tokenRes = await fetch('/session', { method: 'POST' })
  if (!tokenRes.ok) throw new Error(`token server: ${tokenRes.status} ${await tokenRes.text()}`)
  const { value: clientSecret } = await tokenRes.json()

  const mic = await navigator.mediaDevices.getUserMedia({ audio: true })
  const pc = new RTCPeerConnection()
  for (const track of mic.getTracks()) pc.addTrack(track, mic)

  const audioEl = new Audio()
  audioEl.autoplay = true
  pc.ontrack = (e) => { audioEl.srcObject = e.streams[0] }

  const dc = pc.createDataChannel('oai-events')

  dc.onmessage = async (msg) => {
    let ev
    try { ev = JSON.parse(msg.data) } catch { return }
    switch (ev.type) {
      case 'conversation.item.input_audio_transcription.completed':
        onUserCaption?.(ev.transcript?.trim() ?? '')
        break
      case 'response.output_audio_transcript.done':
      case 'response.audio_transcript.done':
        onAssistantCaption?.(ev.transcript?.trim() ?? '')
        break
      case 'output_audio_buffer.started':
        onSpeaking?.(true)
        break
      case 'output_audio_buffer.stopped':
      case 'output_audio_buffer.cleared':
        onSpeaking?.(false)
        break
      case 'response.done': {
        const calls = (ev.response?.output ?? []).filter((item) => item.type === 'function_call')
        for (const call of calls) {
          let result
          try {
            result = onToolCall?.(JSON.parse(call.arguments)) ?? { ok: true }
          } catch (err) {
            result = { ok: false, error: String(err) }
          }
          dc.send(JSON.stringify({
            type: 'conversation.item.create',
            item: { type: 'function_call_output', call_id: call.call_id, output: JSON.stringify(result) },
          }))
        }
        if (calls.length) dc.send(JSON.stringify({ type: 'response.create' }))
        break
      }
      case 'error':
        onError?.(ev.error?.message ?? 'realtime error')
        break
      default:
        break
    }
  }

  const offer = await pc.createOffer()
  await pc.setLocalDescription(offer)

  const sdpRes = await fetch('https://api.openai.com/v1/realtime/calls?model=gpt-realtime', {
    method: 'POST',
    headers: { Authorization: `Bearer ${clientSecret}`, 'Content-Type': 'application/sdp' },
    body: offer.sdp,
  })
  if (!sdpRes.ok) throw new Error(`realtime sdp: ${sdpRes.status} ${await sdpRes.text()}`)
  await pc.setRemoteDescription({ type: 'answer', sdp: await sdpRes.text() })

  return {
    disconnect() {
      dc.close()
      pc.close()
      for (const t of mic.getTracks()) t.stop()
      audioEl.srcObject = null
    },
  }
}
