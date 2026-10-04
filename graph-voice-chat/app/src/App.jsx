import { useGraphStore } from './store/graphStore.js'
import { FRIENDS_FILTER } from './data/mockData.js'
import GraphCanvas from './graph/GraphCanvas.jsx'
import VoiceBar from './voice/VoiceBar.jsx'

const LEGEND = [
  { type: 'topic', label: 'Topic', swatch: 'sw-topic' },
  { type: 'place.restaurant', label: 'Restaurant', swatch: 'sw-restaurant' },
  { type: 'place.hotel', label: 'Hotel', swatch: 'sw-hotel' },
  { type: 'person.friend', label: 'Friend', swatch: 'sw-friend', clickable: true },
  { type: 'source.publication', label: 'Publication', swatch: 'sw-source' },
]

function Legend() {
  const { filters, applyOperations, nodes } = useGraphStore()
  const friendsFilterOn = filters.some((f) => f.require_edge?.from_node_type === 'person.friend')

  const toggleFriends = () => {
    if (!nodes.length) return
    applyOperations({
      operations: friendsFilterOn ? [{ op: 'clear_filter' }] : [FRIENDS_FILTER()],
    })
  }

  return (
    <aside className="legend">
      <div className="legend-title">Legend</div>
      {LEGEND.map((item) => (
        <button
          key={item.type}
          className={`legend-row ${item.clickable ? 'clickable' : ''} ${item.clickable && friendsFilterOn ? 'on' : ''}`}
          onClick={item.clickable ? toggleFriends : undefined}
          title={item.clickable ? 'Toggle: only friend-recommended places' : undefined}
        >
          <span className={`swatch ${item.swatch}`} />
          {item.label}
          {item.clickable && <span className="legend-chip">{friendsFilterOn ? 'filter on' : 'filter'}</span>}
        </button>
      ))}
      <div className="legend-note">Pink edges = friend recommendations. Click a node for details & quotes.</div>
    </aside>
  )
}

export default function App() {
  const { title, mode, setMode, reset, filters } = useGraphStore()
  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-dot" /> Conversation Graph
        </div>
        <div className="title">
          {title}
          {filters.length > 0 && <span className="filter-badge">{filters.map((f) => f.description).join(' · ')}</span>}
        </div>
        <div className="header-actions">
          <div className="mode-toggle">
            <button className={mode === 'simulated' ? 'on' : ''} onClick={() => setMode('simulated')}>
              Simulated
            </button>
            <button className={mode === 'live' ? 'on' : ''} onClick={() => setMode('live')}>
              Live voice
            </button>
          </div>
          <button className="reset" onClick={reset}>Reset</button>
        </div>
      </header>
      <main className="main">
        <GraphCanvas />
        <Legend />
      </main>
      <VoiceBar />
    </div>
  )
}
