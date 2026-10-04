# Conversation Graph — Design Document

A voice-first assistant where **the conversation itself is rendered as a living knowledge graph**. The user talks to the AI (native ChatGPT voice), and everything the AI talks about — places, people, sources, filters — appears as nodes and edges on a canvas that reorganizes itself in real time as the conversation evolves.

---

## 1. Concept

Voice interfaces are great for input but terrible at showing *state*: after three turns you can't remember which five restaurants were mentioned or who recommended what. This prototype fixes that by giving the voice conversation a **spatial memory**:

- Every entity the assistant mentions becomes a **node** (a restaurant, a hotel, a friend, a publication, a neighborhood).
- Every relationship becomes an **edge** ("recommended by", "located in", "reviewed in").
- Every follow-up utterance **mutates the graph**: filtering fades nodes out, refinements grow new branches, focus zooms the camera.

The canonical demo (the one the prototype must nail):

> **User:** "Show me restaurant recommendations in New York."
> → A `New York` topic node appears in the center; 8 restaurant nodes bloom around it; each restaurant is connected to **source nodes** showing where the recommendation comes from (friends, Eater NY, NYT, Michelin, Google Reviews).
>
> **User:** "Show me only the ones my friends recommended."
> → The graph **filters live**: restaurants without a friend edge fade to ghosts, friend nodes glow, the layout re-settles around the 3 surviving restaurants, and the assistant says out loud what changed.

## 2. Core loop

```
 Voice in ──► ChatGPT voice (Realtime API) ──► tool calls (graph ops)
                     │                                │
                     ▼                                ▼
              Spoken answer  ◄────────────  Graph store (nodes/edges)
                                                      │
                                                      ▼
                                            Animated graph canvas
```

The assistant never "describes" the graph in JSON to the user — it **speaks naturally** and simultaneously emits structured tool calls that the client applies to the canvas. Speech and visuals stay in sync because they come from the same model turn.

## 3. Graph model

### Node types

| Type | Shape/color | Examples |
|---|---|---|
| `topic` | Large hub, indigo | "New York", "Restaurants in NYC" |
| `place.restaurant` | Rounded card, teal | Via Carota, Lilia |
| `place.hotel` | Rounded card, amber | The Bowery Hotel |
| `person.friend` | Circle avatar, pink | Dana, Omer, Maya |
| `source.publication` | Square badge, slate | Eater NY, NYT, Michelin |
| `attribute` | Small pill, gray | "$$$", "Italian", "West Village" |

### Edge types

| Type | Style | Meaning |
|---|---|---|
| `recommends` | Solid, colored by source | friend/publication → place |
| `located_in` | Dashed thin | place → neighborhood/topic |
| `refines` | Dotted | follow-up topic → parent topic |
| `attribute_of` | Hairline | attribute pill → place |

Node states: `active` (full opacity), `dimmed` (filter survivor's context), `ghosted` (filtered out — 12% opacity, no labels), `highlighted` (pulse animation on the entities the assistant is currently speaking about).

## 4. Graph operations (the tool contract)

The voice model manipulates the canvas exclusively through **one tool**, `update_graph`, that takes a batch of operations (full schema in `materials/tool-definitions.json`):

- `add_nodes`, `add_edges` — grow the graph
- `apply_filter` — declarative predicate (e.g. "keep places with a `recommends` edge from a `person.friend`"); non-matching nodes ghost instead of being deleted, so "show everything again" is instant
- `clear_filter`, `remove_nodes`
- `highlight` — pulse the nodes currently being spoken about
- `focus` — camera pan/zoom to a subgraph
- `set_title` — headline above the canvas ("Restaurants in NYC — friends only")

One batched tool per turn keeps speech and animation atomic: the client applies ops with staggered 60–120ms entrance animations while the assistant is still talking.

## 5. UI layout

```
┌────────────────────────────────────────────────┐
│  ● Conversation Graph      [title]   [Reset]   │
├────────────────────────────────────────────┬───┤
│                                            │ L │
│                                            │ e │
│              GRAPH CANVAS                  │ g │
│        (force layout, pan/zoom)            │ e │
│                                            │ n │
│                                            │ d │
├────────────────────────────────────────────┴───┤
│  〰〰 waveform    [ 🎤 mic toggle ]   caption   │
└────────────────────────────────────────────────┘
```

- **Canvas**: force-directed layout (d3-force), drag nodes, click a node → detail popover (photo placeholder, blurb, who recommends it).
- **Voice bar**: mic button connects to the Realtime API; live waveform while either side is speaking; running caption of the last utterance (user + assistant).
- **Legend**: node-type key, doubles as manual filter chips (clicking "Friends" applies the same filter as saying it).
- Dark theme, glassy panels; graph is the hero.

## 6. Voice integration — "native ChatGPT voice chat"

The prototype embeds **OpenAI's native voice stack** — the Realtime API (`gpt-realtime`, WebRTC) — which is the same speech-to-speech model that powers ChatGPT's Advanced Voice Mode, with:

- Server VAD for natural barge-in interruptions.
- The `update_graph` tool registered in the session; instructions require a tool call in every turn that changes what's on screen.
- An ephemeral-token endpoint (tiny server route) so the API key never reaches the browser.

**Demo fallback (no API key):** a scripted "simulated voice" mode replays the canonical demo — Web Speech API for TTS, pre-recorded tool-call payloads — so the graph behavior can be shown anywhere. The mode toggle lives in the header.

## 7. Conversation intelligence rules (baked into the voice-session instructions)

1. **Everything spoken gets drawn.** If the assistant mentions an entity, it must exist as a node in the same turn.
2. **Provenance is first-class.** A recommendation is never a bare fact; it always carries a `recommends` edge from a source node ("who says so" is the whole point of the demo).
3. **Filter, don't rebuild.** Narrowing requests ("only my friends'", "only Italian", "under $$$") use `apply_filter` — surviving nodes keep their positions so the user sees continuity.
4. **Speak the diff.** After mutating, the assistant summarizes what changed on screen ("I've faded out five places — the three left are the ones Dana, Omer, and Maya vouch for").
5. **Compound refinements stack.** Filters compose; `clear_filter` restores ghosts.

## 8. Mock data

The prototype ships with a curated NYC dataset (`materials/mock-data.json`): 8 restaurants + 4 hotels, 3 friends with distinct tastes, 4 publications, neighborhoods, price/cuisine attributes, and per-recommendation quotes (shown in the node popover). The voice model is instructed to answer *from this dataset* so the demo is deterministic.

## 9. Tech stack (prototype)

| Concern | Choice | Why |
|---|---|---|
| App | React 18 + Vite, single-page | Fast prototype |
| Graph | React Flow + d3-force custom layout | Interactivity + animated transitions |
| Voice | OpenAI Realtime API over WebRTC | Native ChatGPT voice, tool calling, barge-in |
| Token server | Single Express/Node route `POST /session` | Ephemeral client secrets |
| State | Zustand store of nodes/edges/filters | Simple, animatable |
| Styling | Tailwind, dark theme | Speed |

## 10. Out of scope (prototype)

Real data connectors, auth, persistence beyond page session, mobile layout, multi-user. The graph engine, however, is generic — nothing about it is restaurant-specific.
