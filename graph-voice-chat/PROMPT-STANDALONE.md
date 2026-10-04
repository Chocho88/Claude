# Standalone build prompt for GPT-5.6 (no attachments needed)

Paste everything below the divider into GPT-5.6 as a single message.

---

You are building a polished, demo-ready web prototype called **Conversation Graph**. Work autonomously: scaffold the project, write every file, and finish with run instructions. Do not ask clarifying questions — make sensible choices and note them in the README.

## What the app is

A voice-first AI assistant where the conversation's context is rendered as a **living knowledge graph**. The user talks to ChatGPT's native voice (OpenAI Realtime API, speech-to-speech), and every entity the assistant mentions — restaurants, hotels, friends, publications, neighborhoods — appears as a node on an animated canvas, with edges showing relationships ("recommended by", "located in"). Follow-up utterances mutate the graph in real time: filters fade nodes out, refinements grow new branches.

**The canonical demo, which must work flawlessly:**

1. User says: *"Show me restaurant recommendations in New York."*
   - A central `New York` topic node appears; ~8 restaurant nodes bloom around it with a staggered entrance animation; each restaurant connects to **source nodes** showing where its recommendation comes from — friend avatars (Dana, Omer, Maya) and publications (Eater NY, NYT Food, Michelin Guide, Google Reviews). The assistant simultaneously answers out loud.
2. User says: *"Show me only the ones my friends recommended."*
   - The graph **filters live**: restaurants with no edge from a friend fade to 12%-opacity ghosts (labels hidden), friend nodes glow, the force layout re-settles around the 3 survivors (Via Carota, Lilia, Raku), the header title updates to "Restaurants in NYC — friends only", and the assistant speaks the diff: what was removed and why the survivors made the cut.
3. User says: *"Show everything again"* — ghosts restore. *"Which of those is cheapest?"* — the assistant highlights Raku with a pulse animation while answering.

The same must work for hotels ("show me hotel recommendations…"), and filters must **stack** ("only Italian" then "only my friends'" = both).

## Tech stack (use exactly this)

- **React 18 + Vite + TypeScript**, single-page app, dark theme, Tailwind CSS.
- **Graph:** React Flow (`@xyflow/react`) with a custom **d3-force** simulation for layout (force-many-body, link, collide, centering). Nodes draggable; pan/zoom; animated position transitions when the layout re-settles.
- **State:** Zustand store holding `nodes`, `edges`, `activeFilters[]`, `title`. Filtering is computed state — filtered-out nodes are **ghosted, never deleted**, so clearing a filter is instant.
- **Voice:** OpenAI **Realtime API over WebRTC** (`gpt-realtime` model) — this is the native ChatGPT voice stack: speech-to-speech, server VAD, barge-in. Register the single tool `update_graph` (schema in **Appendix A**) and set the session instructions to **Appendix B**, embedding the full dataset from **Appendix C** into those instructions so the assistant answers only from that dataset.
- **Token endpoint:** a minimal Node/Express server (`server/index.mjs`) with one route, `POST /session`, that mints an ephemeral Realtime client secret using `process.env.OPENAI_API_KEY`. The key must never reach the browser. `npm run dev` should run Vite + the token server together (use `concurrently`), with a Vite proxy for `/session`.
- **Simulated mode (required):** a header toggle "Live voice / Simulated". Simulated mode requires no API key: it plays the canonical demo as a scripted sequence — for each step it shows the user caption, speaks a canned assistant line via the Web Speech API (`speechSynthesis`), and applies a pre-built `update_graph` payload. Pressing space advances to the next step. This mode is the fallback for demoing without credentials and must exercise the exact same graph-op code path as live mode. Script it from the demo in **Appendix D**.

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
  data/mockData.ts             — the Appendix C dataset, typed
  data/demoScript.ts           — simulated-mode steps (captions + canned ops payloads)
server/index.mjs               — POST /session → ephemeral Realtime token
```

**The one invariant:** every visual change flows through `applyOperations(ops)` in the store — whether ops come from a live Realtime tool call or the simulated script. Implement these ops per the Appendix A schema: `add_nodes`, `add_edges`, `apply_filter`, `clear_filter`, `remove_nodes`, `highlight`, `focus`, plus the optional `title`. When a live tool call arrives, apply the ops, then send back a brief tool result (`{"ok": true, "visible_nodes": n}`) so the model can keep talking in the same turn.

`apply_filter` semantics: a filter has a human-readable `description`, optional `keep_node_types` (which types it judges; others untouched), `require_edge` (keep a node only if it has an edge of a given type from a given node type or specific node ids), and `require_meta` (match on `meta` fields; support `price_max`). Filters push onto `activeFilters` and AND together. A node failing any filter is `ghosted`. Sources/friends connected only to ghosted places dim too. `clear_filter` pops all filters.

## Visual design

Dark, premium, "the graph is the hero":

- Background `#0b0e14` with a subtle dot grid; glassy translucent panels.
- Node styling by type — `topic`: large indigo hub with soft glow; `place.restaurant`: teal rounded card with name + neighborhood + price ($–$$$$); `place.hotel`: amber card; `person.friend`: pink circle with initial avatar; `source.publication`: slate square badge; `attribute`: small gray pill.
- Edge styling — `recommends`: solid 2px, pink when from a friend, slate from a publication; `located_in`: dashed; `refines`: dotted; `attribute_of`: hairline. Edges from friends get a slow animated dash flow.
- States: `highlighted` = 2x glow pulse for 3s; `ghosted` = 12% opacity, no label.
- Entrance: new nodes scale from 0 with 60–120ms stagger; layout transitions eased ~500ms.
- Click a node → popover with `detail`, and for places the list of who recommends it **with their quotes** from the dataset.
- Voice bar: circular mic button (idle / connecting / listening / speaking states), canvas-drawn waveform from the audio stream, last user + assistant captions.
- Legend (right side): node-type key; the "Friends" entry is clickable and applies the same friends-only filter as the voice command (proves ops are shared).
- Header: app name, current `title`, mode toggle, Reset button.

## Voice session details

- On mic click: `POST /session` → ephemeral key → WebRTC offer/answer to the Realtime API → attach remote audio track to an `<audio>` element; send mic track.
- Session config: `gpt-realtime`, voice `marin` (or closest available), server VAD with interruption enabled, input+output audio transcription on (for captions), tools = Appendix A, instructions = Appendix B + embedded Appendix C dataset.
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

---

# Appendix A — `update_graph` tool schema

```json
{
  "type": "function",
  "name": "update_graph",
  "description": "Mutate the conversation graph shown to the user. Call this in EVERY turn that changes what should be on screen. Batch all operations for the turn into one call. Never mention node ids or this tool when speaking.",
  "parameters": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "description": "Optional headline above the canvas, e.g. 'Restaurants in NYC — friends only'"
      },
      "operations": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "op": {
              "type": "string",
              "enum": ["add_nodes", "add_edges", "apply_filter", "clear_filter", "remove_nodes", "highlight", "focus"]
            },
            "nodes": {
              "type": "array",
              "description": "For add_nodes",
              "items": {
                "type": "object",
                "properties": {
                  "id": { "type": "string", "description": "stable slug, e.g. 'rest-via-carota'" },
                  "type": {
                    "type": "string",
                    "enum": ["topic", "place.restaurant", "place.hotel", "person.friend", "source.publication", "attribute"]
                  },
                  "label": { "type": "string" },
                  "detail": { "type": "string", "description": "one-line blurb for the popover" },
                  "meta": {
                    "type": "object",
                    "description": "freeform: neighborhood, cuisine, price, quote…",
                    "additionalProperties": true
                  }
                },
                "required": ["id", "type", "label"]
              }
            },
            "edges": {
              "type": "array",
              "description": "For add_edges",
              "items": {
                "type": "object",
                "properties": {
                  "source": { "type": "string" },
                  "target": { "type": "string" },
                  "type": { "type": "string", "enum": ["recommends", "located_in", "refines", "attribute_of"] },
                  "label": { "type": "string", "description": "optional, e.g. 'loved it'" }
                },
                "required": ["source", "target", "type"]
              }
            },
            "filter": {
              "type": "object",
              "description": "For apply_filter. Nodes failing the predicate become ghosted (not deleted). Filters stack until clear_filter.",
              "properties": {
                "description": { "type": "string", "description": "human-readable, e.g. 'friend recommendations only'" },
                "keep_node_types": {
                  "type": "array",
                  "items": { "type": "string" },
                  "description": "node types the filter applies to; others keep current state"
                },
                "require_edge": {
                  "type": "object",
                  "description": "keep a node only if it has such an edge",
                  "properties": {
                    "type": { "type": "string" },
                    "from_node_type": { "type": "string" },
                    "from_node_ids": { "type": "array", "items": { "type": "string" } }
                  }
                },
                "require_meta": {
                  "type": "object",
                  "description": "keep a node only if meta matches, e.g. {\"cuisine\": \"italian\"} or {\"price_max\": 3}",
                  "additionalProperties": true
                }
              },
              "required": ["description"]
            },
            "node_ids": {
              "type": "array",
              "items": { "type": "string" },
              "description": "For remove_nodes / highlight / focus"
            }
          },
          "required": ["op"]
        }
      }
    },
    "required": ["operations"]
  }
}
```

# Appendix B — Voice session instructions (system prompt for the Realtime session)

You are the voice of **Conversation Graph**, a visual assistant. The user talks to you and simultaneously watches a graph canvas that you control through the `update_graph` tool. Your job is to answer naturally in speech AND keep the canvas in sync — the canvas is the user's memory of the conversation.

Hard rules:

1. **Draw everything you say.** Any entity you mention (place, friend, publication, neighborhood, attribute) must exist as a node on the canvas by the end of your turn. Call `update_graph` once per turn, batching all operations, BEFORE or WHILE you speak the answer — never after finishing.
2. **Provenance is first-class.** Never present a recommendation without its source. Every recommended place gets a `recommends` edge from the friend or publication it came from. "Who says so" is the point of this product.
3. **Filter, don't rebuild.** When the user narrows ("only the ones my friends recommended", "only Italian", "under $$$"), use `apply_filter` — never remove_nodes. Filters stack. "Show everything again" means `clear_filter`.
4. **Speak the diff.** After a filter, briefly say what changed on screen: how many faded out, which survived and why. Example: "I've faded out five spots — you're left with Via Carota, Lilia and Raku, the three your friends personally vouch for."
5. **Answer only from the DATASET below.** Do not invent places, friends, sources or quotes. If asked something outside the dataset, say this prototype only knows a curated NYC set, and offer what you have.
6. **Stay invisible as machinery.** Never mention node ids, tools, JSON, filters-as-objects, or "the graph API". Talk like a sharp local friend; refer to the canvas naturally ("I've put them up for you", "the pink lines are your friends").
7. **Keep speech tight.** 2–4 sentences per turn. The canvas carries the detail; you carry the judgment.

Behavior recipes:

- **First recommendations request** ("restaurant recommendations in New York"): add a central `topic` node for New York, all matching places, all their sources, `recommends` edges, `located_in` edges to the topic, then `focus` on the whole set and set the `title`. Mention 2–3 standouts by voice, not all of them.
- **Friends-only filter**: `apply_filter` with `keep_node_types: ["place.restaurant"]` (or hotel, per context) and `require_edge: {"type": "recommends", "from_node_type": "person.friend"}`. Highlight the surviving nodes.
- **Attribute filters** ("Italian", "cheap"): `apply_filter` with `require_meta` (`{"cuisine": "italian"}`, `{"price_max": 2}`).
- **"Which is cheapest / best for X?"**: no new filter — `highlight` the answer node(s) while you explain.
- **Detail question about one place** ("what does Dana say about Lilia?"): `highlight` + `focus` that place, quote the friend's actual quote from the dataset.
- **Topic pivot** ("what about hotels?"): keep the restaurant subgraph, add the hotel nodes and their sources, connect to the same city topic, `focus` on the hotels.
- **Reset / start over**: `remove_nodes` on everything or clear filters, per what the user meant.

DATASET: (embed the full Appendix C JSON here when building the session instructions)

# Appendix C — Mock dataset

```json
{
  "friends": [
    { "id": "friend-dana", "label": "Dana", "detail": "College friend, lives in Brooklyn, obsessed with pasta." },
    { "id": "friend-omer", "label": "Omer", "detail": "Coworker, foodie, keeps a spreadsheet of every meal." },
    { "id": "friend-maya", "label": "Maya", "detail": "Travel buddy, minimalist tastes, hates tourist traps." }
  ],
  "publications": [
    { "id": "src-eater", "label": "Eater NY", "detail": "Eater NY 'Essential Restaurants' list, 2025." },
    { "id": "src-nyt", "label": "NYT Food", "detail": "New York Times restaurant critic picks." },
    { "id": "src-michelin", "label": "Michelin Guide", "detail": "Michelin Guide New York." },
    { "id": "src-google", "label": "Google Reviews", "detail": "4.5+ stars, 1000+ reviews." }
  ],
  "restaurants": [
    {
      "id": "rest-via-carota", "label": "Via Carota",
      "meta": { "neighborhood": "West Village", "cuisine": "italian", "price": 3 },
      "detail": "Rustic Italian, no reservations, legendary svizzerina.",
      "recommended_by": [
        { "source": "friend-dana", "quote": "Best cacio e pepe of my life. Go at 4pm or suffer." },
        { "source": "src-eater" },
        { "source": "src-nyt" }
      ]
    },
    {
      "id": "rest-lilia", "label": "Lilia",
      "meta": { "neighborhood": "Williamsburg", "cuisine": "italian", "price": 3 },
      "detail": "Missy Robbins' pasta temple in a converted auto shop.",
      "recommended_by": [
        { "source": "friend-dana", "quote": "The mafaldini alone is worth the wait." },
        { "source": "friend-omer", "quote": "9.4/10 in my spreadsheet. Highest pasta score ever." },
        { "source": "src-michelin" }
      ]
    },
    {
      "id": "rest-raku", "label": "Raku",
      "meta": { "neighborhood": "East Village", "cuisine": "japanese", "price": 2 },
      "detail": "Tiny handmade-udon shop, cash friendly, zero fuss.",
      "recommended_by": [
        { "source": "friend-maya", "quote": "Quiet, cheap, perfect udon. My favorite spot in the city." }
      ]
    },
    {
      "id": "rest-le-bernardin", "label": "Le Bernardin",
      "meta": { "neighborhood": "Midtown", "cuisine": "french-seafood", "price": 4 },
      "detail": "Eric Ripert's three-Michelin-star seafood institution.",
      "recommended_by": [ { "source": "src-michelin" }, { "source": "src-nyt" } ]
    },
    {
      "id": "rest-katzs", "label": "Katz's Delicatessen",
      "meta": { "neighborhood": "Lower East Side", "cuisine": "deli", "price": 2 },
      "detail": "The pastrami sandwich. Since 1888.",
      "recommended_by": [ { "source": "src-google" }, { "source": "src-eater" } ]
    },
    {
      "id": "rest-superiority-burger", "label": "Superiority Burger",
      "meta": { "neighborhood": "East Village", "cuisine": "vegetarian", "price": 1 },
      "detail": "Cult vegetarian burgers and gelato.",
      "recommended_by": [ { "source": "src-eater" } ]
    },
    {
      "id": "rest-cosme", "label": "Cosme",
      "meta": { "neighborhood": "Flatiron", "cuisine": "mexican", "price": 4 },
      "detail": "Modern Mexican; the duck carnitas and corn husk meringue.",
      "recommended_by": [ { "source": "src-nyt" }, { "source": "src-michelin" } ]
    },
    {
      "id": "rest-joes-pizza", "label": "Joe's Pizza",
      "meta": { "neighborhood": "Greenwich Village", "cuisine": "pizza", "price": 1 },
      "detail": "The classic NY slice, open till 4am.",
      "recommended_by": [ { "source": "src-google" } ]
    }
  ],
  "hotels": [
    {
      "id": "hotel-bowery", "label": "The Bowery Hotel",
      "meta": { "neighborhood": "East Village", "price": 4 },
      "detail": "Old-world lobby, terrace bar, downtown icon.",
      "recommended_by": [
        { "source": "friend-maya", "quote": "Worth it just for the lobby fireplace." },
        { "source": "src-nyt" }
      ]
    },
    {
      "id": "hotel-ace", "label": "Ace Hotel",
      "meta": { "neighborhood": "NoMad", "price": 3 },
      "detail": "Lobby full of laptops by day, DJs by night.",
      "recommended_by": [
        { "source": "friend-omer", "quote": "Stayed twice for work. Great coffee downstairs." }
      ]
    },
    {
      "id": "hotel-wythe", "label": "Wythe Hotel",
      "meta": { "neighborhood": "Williamsburg", "price": 3 },
      "detail": "Converted 1901 factory with Manhattan skyline views.",
      "recommended_by": [ { "source": "src-eater" } ]
    },
    {
      "id": "hotel-pod51", "label": "Pod 51",
      "meta": { "neighborhood": "Midtown East", "price": 1 },
      "detail": "Tiny smart rooms, unbeatable price, rooftop deck.",
      "recommended_by": [ { "source": "src-google" } ]
    }
  ]
}
```

# Appendix D — Canonical demo script (drives Simulated mode)

**Step 1 — Bloom.** User: "Show me restaurant recommendations in New York." Assistant speaks: "Here's what I've got in New York — eight spots worth knowing. The pink lines are recommendations from your friends: Dana swears by Via Carota and Lilia, and Maya's pick is a little udon shop called Raku. The rest come from Eater, the Times, Michelin and Google." Graph: New York hub center; 8 restaurants bloom (staggered); friends Dana/Omer/Maya and publication badges attach with `recommends` edges; dashed `located_in` edges to the hub; title "Restaurants in NYC"; camera fits all.

**Step 2 — Friends-only filter.** User: "Show me only the ones my friends recommended." Assistant speaks: "Done — I've faded out five places. You're left with Via Carota and Lilia from Dana — Omer scored Lilia a nine-point-four — and Raku, Maya's favorite udon spot in the East Village." Graph: friends-only filter; Le Bernardin, Katz's, Superiority Burger, Cosme, Joe's Pizza ghost to 12%; publication badges connected only to ghosts dim; friend nodes glow; three survivors pulse; layout re-settles; title "Restaurants in NYC — friends only".

**Step 3 — Question, no filter.** User: "Which of those is cheapest?" Assistant speaks: "Raku — it's the most affordable of the three, around two dollar signs, and Maya says the handmade udon is the best in the city." Graph: Raku pulses; camera nudges toward it.

**Step 4 — Restore.** User: "Okay, show everything again." Assistant speaks: "Back to the full picture — all eight spots are on the board." Graph: `clear_filter`; ghosts fade back in at kept positions; title "Restaurants in NYC".

**Step 5 — Pivot to hotels.** User: "What about hotels?" Assistant speaks: "Adding four — Maya loves The Bowery Hotel for the lobby alone, and Omer's stayed at the Ace twice. The Wythe and Pod 51 round it out from Eater and Google." Graph: 4 amber hotel nodes join the same hub with their sources; camera focuses the hotel cluster; restaurants remain.
