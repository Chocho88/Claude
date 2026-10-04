// Token server: the only place the OpenAI API key lives. Mints short-lived
// Realtime client secrets, with the session (instructions + tools + dataset)
// configured server-side so the browser can't tamper with it.

import express from 'express'
import { readFileSync } from 'node:fs'
import { REALTIME_SESSION } from '../src/voice/sessionConfig.js'

// minimal .env loader so live mode works on any Node >= 18
try {
  for (const line of readFileSync(new URL('../.env', import.meta.url), 'utf8').split('\n')) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/)
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '')
  }
} catch { /* no .env — Simulated mode still works */ }

const app = express()
const PORT = process.env.PORT || 8787

app.post('/session', async (_req, res) => {
  const key = process.env.OPENAI_API_KEY
  if (!key) {
    res.status(500).send('OPENAI_API_KEY is not set — use Simulated mode, or add the key to .env')
    return
  }
  try {
    const r = await fetch('https://api.openai.com/v1/realtime/client_secrets', {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ session: REALTIME_SESSION }),
    })
    const body = await r.text()
    res.status(r.status).type('application/json').send(body)
  } catch (err) {
    res.status(502).send(String(err))
  }
})

app.listen(PORT, () => console.log(`[token server] listening on :${PORT}`))
