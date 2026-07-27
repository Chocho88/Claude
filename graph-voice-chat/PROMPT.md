# Build Prompt for GPT-5.6

Paste everything below the line into GPT-5.6, and attach the three files from `materials/`:
`tool-definitions.json`, `mock-data.json`, `voice-instructions.md`.
(If you can't attach files, paste their contents at the end of the prompt under the matching headings.)

---

You are building a polished, demo-ready web prototype called **Conversation Graph**. Work autonomously: scaffold the project, write every file, and finish with run instructions. Do not ask clarifying questions — make sensible choices and note them in the README.

## What the app is

A voice-first AI assistant where the conversation's context is rendered as a **living knowledge graph**. The user talks to ChatGPT's native voice (OpenAI Realtime API, speech-to-speech), and every entity the assistant mentions — restaurants, hotels, friends, publications, neighborhoods — appears as a node on an animated canvas, with edges showing relationships ("recommended by", "located in"). Follow-up utterances mutate the graph in real time: filters fade nodes out, refinements grow new branches.

**The canonical demo, which must work flawlessly:**

1. User says: *"Show me restaurant recommendations in New York."*
   → A central `New York` topic node appears; ~8 restaurant nodes bloom around it with a staggered entrance animation; each restaurant connects to **source nodes** showing where its recommendation comes from — friend avatars (Dana, Omer, Maya) and publications (Eater NY, NYT Food, Michelin Guide, Google Reviews). The assistant simultaneously answers out loud.
2. User says: *"Show me only the ones my friends recommended."*
   → The graph **filters live**: restaurants with no edge from a friend fade to 12%-opacity ghosts (labels hidden), friend nodes glow, the force layout re-settles around the 3 survivors (Via Carota, Lilia, Raku), the header title updates to "Restaurants in NYC — friends only", and the assistant speaks the diff: what was removed and why the survivors made the cut.
3. User says: *"Show everything again"* → ghosts restore. *"Which of those is cheapest?"* → the assistant highlights Raku with a pulse animation while answering.

The same must work for hotels ("show me hotel recommendations…"), and filters must **stack** ("only Italian" then "only my friends'" = both).

## Tech stack (use exactly this)

- **React 18 + Vite + TypeScript**, single-page app, dark theme, Tailwind CSS.
- **Graph:** React Flow (`@xyflow/react`) with a custom **d3-force** simulation for layout (force-many-body, link, collide, centering). Nodes draggable; pan/zoom; animated position transitions when the layout re-settles.
- **State:** Zustand store holding `nodes`, `edges`, `activeFilters[]`, `title`. Filtering is computed state — filtered-out nodes are **ghosted, never deleted**, so clearing a filter is instant.
- **Voice:** OpenAI **Realtime API over WebRTC** (`gpt-realtime` model) — this is the native ChatGPT voice stack: speech-to-speech, server VAD, barge-in. Register the single tool `update_graph` (schema in the attached `tool-definitions.json`) and set the session instructions to the attached `voice-instructions.md`, embedding the full contents of `mock-data.json` into those instructions so the assistant answers only from that dataset.
- **Token endpoint:** a minimal Node/Express server (`server/index.mjs`) with one route, `POST /session`, that mints an ephemeral Realtime client secret using `process.env.OPENAI_API_KEY`. The key must never reach the browser. `npm run dev` should run Vite + the token server together (use `concurrently`), with a Vite proxy for `/session`.
- **Simulated mode (required):** a header toggle "Live voice / Simulated". Simulated mode requires no API key: it plays the canonical demo as a scripted sequence — for each step it shows the user caption, speaks a canned assistant line via the Web Speech API (`speechSynthesis`), and applies a pre-built `update_graph` payload. Pressing space advances to the next step. This mode is the fallback for demoing without credentials and must exercise the exact same graph-op code path as live mode.

## Architecture

```
src/
  main.tsx / App.tsx          — layout: header, canvas, voice bar, legend
  store/graphStore.ts          — Zustand: nodes, edges, filters, title + applyOperations(ops)
  graph/GraphCanvas.tsx        — React Flow canvas + d3-force layout hook
  graph/nodeTypes/*.tsx        — custom node renderers per node type
  graph/edgeTypes.tsx          — styled edges per edge type
  voice/realtime.ts            — WebRTC session: connect, tool-call handling, transcripts
  voice/simulated.ts           — scripted demo driver (same applyOperations path)
  voice/VoiceBar.tsx           — mic button, waveform, live captions
  data/mockData.ts             — the attached mock-data.json, typed
  data/demoScript.ts           — simulated-mode steps (captions + canned ops payloads)
server/index.mjs               — POST /session → ephemeral Realtime token
```

**The one invariant:** every visual change flows through `applyOperations(ops)` in the store — whether ops come from a live Realtime tool call or the simulated script. Implement these ops per the attached schema: `add_nodes`, `add_edges`, `apply_filter`, `clear_filter`, `remove_nodes`, `highlight`, `focus`, plus the optional `title`. When a live tool call arrives, apply the ops, then send back a brief tool result (`{"ok": true, "visible_nodes": n}`) so the model can keep talking in the same turn.

`apply_filter` semantics: a filter has a human-readable `description`, optional `keep_node_types` (which types it judges; others untouched), `require_edge` (keep a node only if it has an edge of a given type from a given node type or specific node ids), and `require_meta` (match on `meta` fields; support `price_max`). Filters push onto `activeFilters` and AND together. A node failing any filter → `ghosted`. Sources/friends connected only to ghosted places dim too. `clear_filter` pops all filters.

## Visual design

Dark, premium, "the graph is the hero":

- Background `#0b0e14` with a subtle dot grid; glassy translucent panels.
- Node styling by type — `topic`: large indigo hub with soft glow; `place.restaurant`: teal rounded card with name + neighborhood + price ($–$$$$); `place.hotel`: amber card; `person.friend`: pink circle with initial avatar; `source.publication`: slate square badge; `attribute`: small gray pill.
- Edge styling — `recommends`: solid 2px, pink when from a friend, slate from a publication; `located_in`: dashed; `refines`: dotted; `attribute_of`: hairline. Edges from friends get a slow animated dash flow.
- States: `highlighted` = 2× glow pulse for 3s; `ghosted` = 12% opacity, no label, excluded from force collisions shrink.
- Entrance: new nodes scale from 0 with 60–120ms stagger; layout transitions eased ~500ms.
- Click a node → popover with `detail`, and for places the list of who recommends it **with their quotes** from the dataset.
- Voice bar: circular mic button (idle / connecting / listening / speaking states), canvas-drawn waveform from the audio stream, last user + assistant captions.
- Legend (right side): node-type key; the "Friends" entry is clickable and applies the same friends-only filter as the voice command (proves ops are shared).
- Header: app name, current `title`, mode toggle, Reset button.

## Voice session details

- On mic click: `POST /session` → ephemeral key → WebRTC offer/answer to the Realtime API → attach remote audio track to an `<audio>` element; send mic track.
- Session config: `gpt-realtime`, voice `marin` (or closest available), server VAD with interruption enabled, input+output audio transcription on (for captions), tools = attached `tool-definitions.json`, instructions = attached `voice-instructions.md` + embedded dataset.
- Handle events: tool call deltas → parse complete call → `applyOperations` → tool result; transcription events → captions; connection errors → toast with a "switch to Simulated mode" action.

## Deliverables & acceptance

- Complete runnable project: `npm install && npm run dev` (plus `OPENAI_API_KEY` in `.env` for live mode). README with setup, both modes, and a mermaid architecture sketch.
- Acceptance checklist (verify each before finishing):
  1. Simulated mode plays the full canonical demo end-to-end with animations and TTS.
  2. Live mode: speaking the two demo utterances produces the bloom and the friends-only filter, with speech and visuals in the same turn.
  3. Filters stack and clear; ghosts restore with positions intact.
  4. Node popovers show recommendation quotes; legend chip applies the friends filter.
  5. No API key in client code; app builds clean with `npm run build`; no console errors.

Build it now, file by file, complete — no placeholders or TODOs.
