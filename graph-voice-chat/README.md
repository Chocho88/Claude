# Conversation Graph — build-prompt package

Everything needed to have GPT-5.6 build a prototype of a voice-first assistant whose conversation context is rendered as a live, filterable knowledge graph (native ChatGPT voice via the OpenAI Realtime API).

## Contents

| File | What it is |
|---|---|
| `DESIGN.md` | Full product + UX + architecture design: concept, graph model, tool contract, UI layout, voice integration, conversation rules. |
| `PROMPT.md` | **The prompt.** Paste into GPT-5.6 (attaching the three materials files) and it builds the complete runnable prototype. |
| `materials/tool-definitions.json` | The `update_graph` function schema the voice model uses to mutate the canvas. |
| `materials/voice-instructions.md` | System instructions for the Realtime voice session (behavior rules + recipes). |
| `materials/mock-data.json` | Curated NYC dataset: 8 restaurants, 4 hotels, 3 friends, 4 publications, quotes. |
| `materials/demo-script.md` | The canonical 5-step demo (also drives the prototype's no-API-key Simulated mode). |

## How to use

1. Open GPT-5.6.
2. Attach `materials/tool-definitions.json`, `materials/mock-data.json`, `materials/voice-instructions.md`.
3. Paste the body of `PROMPT.md` (everything below its divider) and send.
4. Run the generated project: `npm install && npm run dev`. Add `OPENAI_API_KEY` to `.env` for live voice, or use the built-in Simulated mode to demo without a key.

## The demo in one breath

Say *"Show me restaurant recommendations in New York"* → the graph blooms: New York hub, 8 restaurants, each wired to the friend or publication that recommends it. Say *"Show me only the ones my friends recommended"* → five restaurants fade to ghosts, the three friend-backed ones survive and pulse, and the assistant explains the diff out loud.
