import { create } from 'zustand'

// Every visual change in the app — from a live Realtime tool call, the
// simulated demo driver, or a legend chip — flows through applyOperations.

let highlightTimer = null

function metaMatches(meta = {}, require_meta = {}) {
  for (const [key, want] of Object.entries(require_meta)) {
    if (key === 'price_max') {
      if (typeof meta.price !== 'number' || meta.price > want) return false
    } else if (String(meta[key] ?? '').toLowerCase() !== String(want).toLowerCase()) {
      return false
    }
  }
  return true
}

function nodePassesFilter(node, filter, nodes, edges) {
  const applies = !filter.keep_node_types?.length || filter.keep_node_types.includes(node.type)
  if (!applies) return true
  if (filter.require_meta && !metaMatches(node.meta, filter.require_meta)) return false
  if (filter.require_edge) {
    const req = filter.require_edge
    const ok = edges.some((e) => {
      if (e.target !== node.id) return false
      if (req.type && e.type !== req.type) return false
      if (req.from_node_ids?.length && !req.from_node_ids.includes(e.source)) return false
      if (req.from_node_type) {
        const src = nodes.find((n) => n.id === e.source)
        if (!src || src.type !== req.from_node_type) return false
      }
      return true
    })
    if (!ok) return false
  }
  return true
}

// Computes per-node visual state from the active filters. Filtered-out nodes
// ghost (never deleted); sources/friends whose every place is ghosted dim.
export function computeStates(nodes, edges, filters) {
  const states = {}
  const isPlace = (n) => n.type.startsWith('place.')
  for (const n of nodes) {
    states[n.id] =
      filters.length && !filters.every((f) => nodePassesFilter(n, f, nodes, edges)) ? 'ghosted' : 'active'
  }
  if (filters.length) {
    for (const n of nodes) {
      if (n.type !== 'person.friend' && n.type !== 'source.publication') continue
      const targets = edges.filter((e) => e.source === n.id && e.type === 'recommends')
      if (targets.length && targets.every((e) => states[e.target] === 'ghosted')) states[n.id] = 'dimmed'
    }
    for (const n of nodes) {
      if (n.type === 'person.friend' && states[n.id] === 'active' &&
          edges.some((e) => e.source === n.id && states[e.target] === 'active' && isPlace(nodes.find((m) => m.id === e.target) ?? { type: '' }))) {
        states[n.id] = 'glowing'
      }
    }
  }
  return states
}

export const useGraphStore = create((set, get) => ({
  nodes: [],
  edges: [],
  filters: [],
  title: '',
  highlightIds: [],
  focusRequest: null, // { ids, ts } consumed by the canvas camera
  mode: 'simulated', // 'simulated' | 'live'
  captions: { user: '', assistant: '' },
  speaking: false,

  setMode: (mode) => set({ mode }),
  setCaptions: (partial) => set((s) => ({ captions: { ...s.captions, ...partial } })),
  setSpeaking: (speaking) => set({ speaking }),

  reset: () =>
    set({ nodes: [], edges: [], filters: [], title: '', highlightIds: [], focusRequest: null, captions: { user: '', assistant: '' } }),

  applyOperations: (payload) => {
    const ops = payload.operations ?? []
    let { nodes, edges, filters, highlightIds, focusRequest, title } = get()
    nodes = [...nodes]
    edges = [...edges]
    filters = [...filters]

    for (const op of ops) {
      switch (op.op) {
        case 'add_nodes':
          for (const n of op.nodes ?? []) {
            if (!nodes.some((x) => x.id === n.id)) nodes.push({ ...n, addedAt: performance.now() })
          }
          break
        case 'add_edges':
          for (const e of op.edges ?? []) {
            if (!edges.some((x) => x.source === e.source && x.target === e.target && x.type === e.type)) {
              edges.push(e)
            }
          }
          break
        case 'apply_filter':
          if (op.filter) filters.push(op.filter)
          break
        case 'clear_filter':
          filters = []
          break
        case 'remove_nodes': {
          const gone = new Set(op.node_ids ?? [])
          nodes = nodes.filter((n) => !gone.has(n.id))
          edges = edges.filter((e) => !gone.has(e.source) && !gone.has(e.target))
          break
        }
        case 'highlight':
          highlightIds = op.node_ids ?? []
          clearTimeout(highlightTimer)
          highlightTimer = setTimeout(() => set({ highlightIds: [] }), 3000)
          break
        case 'focus':
          focusRequest = { ids: op.node_ids ?? [], ts: performance.now() }
          break
        default:
          break
      }
    }
    if (payload.title !== undefined) title = payload.title
    set({ nodes, edges, filters, highlightIds, focusRequest, title })
    const states = computeStates(nodes, edges, filters)
    return { ok: true, visible_nodes: Object.values(states).filter((s) => s !== 'ghosted').length }
  },
}))
