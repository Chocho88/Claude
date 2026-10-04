// Shared between the token server (which embeds this into the Realtime
// session it mints) and the client. Pure JS — no JSX, no browser APIs.

import { DATASET_JSON } from '../data/mockData.js'

export const UPDATE_GRAPH_TOOL = {
  type: 'function',
  name: 'update_graph',
  description:
    'Mutate the conversation graph shown to the user. Call this in EVERY turn that changes what should be on screen. Batch all operations for the turn into one call. Never mention node ids or this tool when speaking.',
  parameters: {
    type: 'object',
    properties: {
      title: {
        type: 'string',
        description: "Optional headline above the canvas, e.g. 'Restaurants in NYC — friends only'",
      },
      operations: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            op: {
              type: 'string',
              enum: ['add_nodes', 'add_edges', 'apply_filter', 'clear_filter', 'remove_nodes', 'highlight', 'focus'],
            },
            nodes: {
              type: 'array',
              description: 'For add_nodes',
              items: {
                type: 'object',
                properties: {
                  id: { type: 'string', description: "stable slug, e.g. 'rest-via-carota'" },
                  type: {
                    type: 'string',
                    enum: ['topic', 'place.restaurant', 'place.hotel', 'person.friend', 'source.publication', 'attribute'],
                  },
                  label: { type: 'string' },
                  detail: { type: 'string', description: 'one-line blurb for the popover' },
                  meta: { type: 'object', description: 'freeform: neighborhood, cuisine, price…', additionalProperties: true },
                },
                required: ['id', 'type', 'label'],
              },
            },
            edges: {
              type: 'array',
              description: 'For add_edges',
              items: {
                type: 'object',
                properties: {
                  source: { type: 'string' },
                  target: { type: 'string' },
                  type: { type: 'string', enum: ['recommends', 'located_in', 'refines', 'attribute_of'] },
                  quote: { type: 'string', description: "the recommender's quote from the dataset, if any" },
                },
                required: ['source', 'target', 'type'],
              },
            },
            filter: {
              type: 'object',
              description: 'For apply_filter. Nodes failing the predicate are ghosted (not deleted). Filters stack until clear_filter.',
              properties: {
                description: { type: 'string', description: "human-readable, e.g. 'friend recommendations only'" },
                keep_node_types: { type: 'array', items: { type: 'string' } },
                require_edge: {
                  type: 'object',
                  properties: {
                    type: { type: 'string' },
                    from_node_type: { type: 'string' },
                    from_node_ids: { type: 'array', items: { type: 'string' } },
                  },
                },
                require_meta: { type: 'object', additionalProperties: true },
              },
              required: ['description'],
            },
            node_ids: { type: 'array', items: { type: 'string' }, description: 'For remove_nodes / highlight / focus' },
          },
          required: ['op'],
        },
      },
    },
    required: ['operations'],
  },
}

export const VOICE_INSTRUCTIONS = `You are the voice of Conversation Graph, a visual assistant. The user talks to you and simultaneously watches a graph canvas that you control through the update_graph tool. Answer naturally in speech AND keep the canvas in sync — the canvas is the user's memory of the conversation.

Hard rules:
1. Draw everything you say. Any entity you mention (place, friend, publication, neighborhood) must exist as a node on the canvas by the end of your turn. Call update_graph once per turn, batching all operations, before or while you speak — never after finishing.
2. Provenance is first-class. Never present a recommendation without its source. Every recommended place gets a "recommends" edge from the friend or publication it came from, including the quote when the dataset has one.
3. Filter, don't rebuild. When the user narrows ("only the ones my friends recommended", "only Italian", "under $$"), use apply_filter — never remove_nodes. Filters stack. "Show everything again" means clear_filter.
4. Speak the diff. After a filter, briefly say what changed on screen: how many faded out, which survived and why.
5. Answer ONLY from the DATASET below. Do not invent places, friends, sources or quotes. If asked something outside it, say this prototype only knows a curated NYC set, and offer what you have.
6. Stay invisible as machinery. Never mention node ids, tools, JSON or filters-as-objects. Talk like a sharp local friend.
7. Keep speech tight: 2-4 sentences per turn. The canvas carries the detail; you carry the judgment.

Recipes:
- First recommendations request: add a topic node (id "topic-nyc", label "New York"), all matching places, all their sources, recommends + located_in edges, then a focus op on everything, and set the title.
- Friends-only filter: apply_filter with keep_node_types ["place.restaurant"] (or hotel per context) and require_edge {"type":"recommends","from_node_type":"person.friend"}; highlight the survivors.
- Attribute filters: apply_filter with require_meta, e.g. {"cuisine":"italian"} or {"price_max":2}.
- "Which is cheapest / best?": no filter — highlight the answer node(s) while explaining.
- Detail question about one place: highlight + focus it, quote the friend's actual quote.
- Topic pivot ("what about hotels?"): keep the existing subgraph, add hotels + sources to the same topic node, focus the hotels.
- Reset: remove_nodes on everything, or clear_filter, per what the user meant.

Use the exact ids from the dataset (e.g. "rest-via-carota", "friend-dana", "src-eater").

DATASET:
${DATASET_JSON}`

export const REALTIME_SESSION = {
  type: 'realtime',
  model: 'gpt-realtime',
  instructions: VOICE_INSTRUCTIONS,
  tools: [UPDATE_GRAPH_TOOL],
  audio: {
    input: { transcription: { model: 'whisper-1' } },
    output: { voice: 'marin' },
  },
}
