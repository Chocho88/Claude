import { useEffect, useMemo, useRef, useState } from 'react'
import { forceSimulation, forceLink, forceManyBody, forceCollide, forceX, forceY } from 'd3-force'
import { useGraphStore, computeStates } from '../store/graphStore.js'

const COLLIDE = {
  topic: 64,
  'place.restaurant': 62,
  'place.hotel': 62,
  'person.friend': 40,
  'source.publication': 46,
  attribute: 28,
}
const LINK_DIST = { recommends: 110, located_in: 150, refines: 130, attribute_of: 70 }

function priceSigns(price) {
  return typeof price === 'number' ? '$'.repeat(price) : ''
}

function NodeBody({ node }) {
  switch (node.type) {
    case 'topic':
      return <div className="node-topic">{node.label}</div>
    case 'place.restaurant':
    case 'place.hotel':
      return (
        <div className={`node-place ${node.type === 'place.hotel' ? 'hotel' : 'restaurant'}`}>
          <div className="place-name">{node.label}</div>
          <div className="place-sub">
            <span>{node.meta?.neighborhood}</span>
            <span className="place-price">{priceSigns(node.meta?.price)}</span>
          </div>
        </div>
      )
    case 'person.friend':
      return (
        <div className="node-friend">
          <div className="friend-avatar">{node.label[0]}</div>
          <div className="friend-name">{node.label}</div>
        </div>
      )
    case 'source.publication':
      return <div className="node-source">{node.label}</div>
    default:
      return <div className="node-attr">{node.label}</div>
  }
}

function Popover({ node, nodes, edges, pos, onClose }) {
  const recs = edges
    .filter((e) => e.type === 'recommends' && e.target === node.id)
    .map((e) => ({ source: nodes.find((n) => n.id === e.source), quote: e.quote }))
  return (
    <div className="popover" style={{ left: pos.x + 16, top: pos.y + 16 }}>
      <div className="popover-head">
        <strong>{node.label}</strong>
        <button className="popover-close" onClick={onClose}>×</button>
      </div>
      {node.detail && <p className="popover-detail">{node.detail}</p>}
      {node.meta?.neighborhood && (
        <p className="popover-meta">
          {node.meta.neighborhood}
          {node.meta.cuisine ? ` · ${node.meta.cuisine}` : ''} · {priceSigns(node.meta.price)}
        </p>
      )}
      {recs.length > 0 && (
        <div className="popover-recs">
          <div className="popover-recs-title">Recommended by</div>
          {recs.map((r, i) => (
            <div key={i} className="popover-rec">
              <span className={r.source?.type === 'person.friend' ? 'rec-friend' : 'rec-pub'}>
                {r.source?.label}
              </span>
              {r.quote && <span className="rec-quote">“{r.quote}”</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function GraphCanvas() {
  const { nodes, edges, filters, highlightIds, focusRequest } = useGraphStore()
  const containerRef = useRef(null)
  const simRef = useRef(null)
  const simNodesRef = useRef(new Map()) // id -> mutable sim node
  const cameraRef = useRef({ x: 0, y: 0, k: 1, initialized: false })
  const cameraAnimRef = useRef(null)
  const dragRef = useRef(null)
  const [, setTick] = useState(0)
  const [selected, setSelected] = useState(null)

  const states = useMemo(() => computeStates(nodes, edges, filters), [nodes, edges, filters])

  // --- force simulation sync ---
  useEffect(() => {
    const simNodes = simNodesRef.current
    const live = new Set(nodes.map((n) => n.id))
    for (const id of [...simNodes.keys()]) if (!live.has(id)) simNodes.delete(id)

    let batchIndex = 0
    for (const n of nodes) {
      if (!simNodes.has(n.id)) {
        // spawn near a linked node that already exists, else near origin
        const link = edges.find(
          (e) => (e.source === n.id && simNodes.has(e.target)) || (e.target === n.id && simNodes.has(e.source)),
        )
        const anchor = link ? simNodes.get(link.source === n.id ? link.target : link.source) : null
        const angle = Math.PI * 2 * (batchIndex / 8) + batchIndex
        simNodes.set(n.id, {
          id: n.id,
          type: n.type,
          x: (anchor?.x ?? 0) + Math.cos(angle) * 30,
          y: (anchor?.y ?? 0) + Math.sin(angle) * 30,
          entranceDelay: Math.min(batchIndex * 90, 1200),
        })
        batchIndex += 1
      }
    }

    const simNodeList = [...simNodes.values()]
    const links = edges
      .filter((e) => simNodes.has(e.source) && simNodes.has(e.target))
      .map((e) => ({ source: e.source, target: e.target, type: e.type }))

    if (!simRef.current) {
      simRef.current = forceSimulation(simNodeList)
        .force('charge', forceManyBody().strength(-420))
        .force('x', forceX(0).strength(0.03))
        .force('y', forceY(0).strength(0.03))
        .on('tick', () => setTick((t) => t + 1))
    } else {
      simRef.current.nodes(simNodeList)
    }
    simRef.current
      .force('link', forceLink(links).id((d) => d.id).distance((l) => LINK_DIST[l.type] ?? 120).strength(0.5))
      .force('collide', forceCollide().radius((d) => COLLIDE[d.type] ?? 40).strength(0.9))
    if (batchIndex > 0 || links.length) simRef.current.alpha(0.9).restart()
  }, [nodes, edges])

  useEffect(() => () => simRef.current?.stop(), [])

  // --- camera ---
  const applyCamera = () => setTick((t) => t + 1)

  const animateCameraTo = (target) => {
    cancelAnimationFrame(cameraAnimRef.current)
    const from = { ...cameraRef.current }
    const start = performance.now()
    const dur = 550
    const step = (now) => {
      const p = Math.min(1, (now - start) / dur)
      const e = 1 - Math.pow(1 - p, 3)
      cameraRef.current = {
        ...cameraRef.current,
        x: from.x + (target.x - from.x) * e,
        y: from.y + (target.y - from.y) * e,
        k: from.k + (target.k - from.k) * e,
      }
      applyCamera()
      if (p < 1) cameraAnimRef.current = requestAnimationFrame(step)
    }
    cameraAnimRef.current = requestAnimationFrame(step)
  }

  const fitToIds = (ids) => {
    const el = containerRef.current
    if (!el) return
    const simNodes = simNodesRef.current
    const pool = (ids?.length ? ids : [...simNodes.keys()]).map((id) => simNodes.get(id)).filter(Boolean)
    if (!pool.length) return
    const xs = pool.map((n) => n.x)
    const ys = pool.map((n) => n.y)
    const pad = 120
    const minX = Math.min(...xs) - pad, maxX = Math.max(...xs) + pad
    const minY = Math.min(...ys) - pad, maxY = Math.max(...ys) + pad
    const w = el.clientWidth, h = el.clientHeight
    const k = Math.min(1.3, Math.max(0.3, Math.min(w / (maxX - minX), h / (maxY - minY))))
    animateCameraTo({ x: w / 2 - ((minX + maxX) / 2) * k, y: h / 2 - ((minY + maxY) / 2) * k, k })
  }

  useEffect(() => {
    const el = containerRef.current
    if (el && !cameraRef.current.initialized) {
      cameraRef.current = { x: el.clientWidth / 2, y: el.clientHeight / 2, k: 1, initialized: true }
      applyCamera()
    }
  }, [])

  useEffect(() => {
    if (!focusRequest) return
    // let the layout settle a moment before framing the shot
    const t1 = setTimeout(() => fitToIds(focusRequest.ids), 350)
    const t2 = setTimeout(() => fitToIds(focusRequest.ids), 1200)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [focusRequest]) // eslint-disable-line react-hooks/exhaustive-deps

  // --- pointer interactions ---
  const toWorld = (clientX, clientY) => {
    const rect = containerRef.current.getBoundingClientRect()
    const { x, y, k } = cameraRef.current
    return { x: (clientX - rect.left - x) / k, y: (clientY - rect.top - y) / k }
  }

  const onPointerDown = (e, nodeId = null) => {
    e.currentTarget.setPointerCapture?.(e.pointerId)
    if (nodeId) {
      const sn = simNodesRef.current.get(nodeId)
      dragRef.current = { kind: 'node', id: nodeId, moved: false }
      if (sn) { sn.fx = sn.x; sn.fy = sn.y }
      simRef.current?.alphaTarget(0.25).restart()
      e.stopPropagation()
    } else {
      dragRef.current = { kind: 'pan', startX: e.clientX, startY: e.clientY, cam: { ...cameraRef.current } }
    }
  }

  const onPointerMove = (e) => {
    const drag = dragRef.current
    if (!drag) return
    if (drag.kind === 'node') {
      const sn = simNodesRef.current.get(drag.id)
      if (sn) {
        const p = toWorld(e.clientX, e.clientY)
        sn.fx = p.x
        sn.fy = p.y
        drag.moved = true
      }
    } else {
      cameraRef.current.x = drag.cam.x + (e.clientX - drag.startX)
      cameraRef.current.y = drag.cam.y + (e.clientY - drag.startY)
      applyCamera()
    }
  }

  const onPointerUp = (e) => {
    const drag = dragRef.current
    dragRef.current = null
    if (drag?.kind === 'node') {
      const sn = simNodesRef.current.get(drag.id)
      if (sn) { sn.fx = null; sn.fy = null }
      simRef.current?.alphaTarget(0)
      if (!drag.moved) {
        const node = nodes.find((n) => n.id === drag.id)
        if (node) {
          const rect = containerRef.current.getBoundingClientRect()
          setSelected({ id: node.id, pos: { x: e.clientX - rect.left, y: e.clientY - rect.top } })
        }
      }
    }
  }

  const onWheel = (e) => {
    const rect = containerRef.current.getBoundingClientRect()
    const { x, y, k } = cameraRef.current
    const factor = Math.exp(-e.deltaY * 0.0015)
    const nk = Math.min(2.5, Math.max(0.2, k * factor))
    const cx = e.clientX - rect.left
    const cy = e.clientY - rect.top
    cameraRef.current = {
      ...cameraRef.current,
      k: nk,
      x: cx - ((cx - x) / k) * nk,
      y: cy - ((cy - y) / k) * nk,
    }
    applyCamera()
  }

  // --- render ---
  const { x: camX, y: camY, k: camK } = cameraRef.current
  const simNodes = simNodesRef.current
  const friendIds = new Set(nodes.filter((n) => n.type === 'person.friend').map((n) => n.id))
  const selectedNode = selected ? nodes.find((n) => n.id === selected.id) : null

  return (
    <div
      ref={containerRef}
      className="canvas"
      onPointerDown={(e) => onPointerDown(e)}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onWheel={onWheel}
    >
      <div className="world" style={{ transform: `translate(${camX}px, ${camY}px) scale(${camK})` }}>
        <svg className="edges" overflow="visible">
          {edges.map((e, i) => {
            const s = simNodes.get(e.source)
            const t = simNodes.get(e.target)
            if (!s || !t) return null
            const ghost = states[e.source] === 'ghosted' || states[e.target] === 'ghosted'
            const dim = states[e.source] === 'dimmed' || states[e.target] === 'dimmed'
            const cls = [
              'edge',
              `edge-${e.type}`,
              e.type === 'recommends' && friendIds.has(e.source) ? 'edge-friend' : '',
              ghost ? 'edge-ghost' : dim ? 'edge-dim' : '',
            ].join(' ')
            return <line key={i} className={cls} x1={s.x} y1={s.y} x2={t.x} y2={t.y} />
          })}
        </svg>
        {nodes.map((n) => {
          const sn = simNodes.get(n.id)
          if (!sn) return null
          const cls = [
            'gnode',
            `state-${states[n.id] ?? 'active'}`,
            highlightIds.includes(n.id) ? 'highlighted' : '',
          ].join(' ')
          return (
            <div
              key={n.id}
              className={cls}
              style={{
                transform: `translate(${sn.x}px, ${sn.y}px)`,
                animationDelay: `${sn.entranceDelay}ms`,
              }}
              onPointerDown={(e) => onPointerDown(e, n.id)}
            >
              <NodeBody node={n} />
            </div>
          )
        })}
      </div>
      {nodes.length === 0 && (
        <div className="canvas-empty">
          <div className="canvas-empty-title">Nothing on the board yet</div>
          <div>Start the demo, or connect live voice and ask for recommendations in New York.</div>
        </div>
      )}
      {selectedNode && (
        <Popover
          node={selectedNode}
          nodes={nodes}
          edges={edges}
          pos={selected.pos}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}
