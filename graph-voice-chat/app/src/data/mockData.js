// Curated demo dataset. The voice assistant is instructed to answer only from
// this data so the demo is deterministic.

export const FRIENDS = [
  { id: 'friend-dana', label: 'Dana', detail: 'College friend, lives in Brooklyn, obsessed with pasta.' },
  { id: 'friend-omer', label: 'Omer', detail: 'Coworker, foodie, keeps a spreadsheet of every meal.' },
  { id: 'friend-maya', label: 'Maya', detail: 'Travel buddy, minimalist tastes, hates tourist traps.' },
]

export const PUBLICATIONS = [
  { id: 'src-eater', label: 'Eater NY', detail: "Eater NY 'Essential Restaurants' list, 2025." },
  { id: 'src-nyt', label: 'NYT Food', detail: 'New York Times restaurant critic picks.' },
  { id: 'src-michelin', label: 'Michelin Guide', detail: 'Michelin Guide New York.' },
  { id: 'src-google', label: 'Google Reviews', detail: '4.5+ stars, 1000+ reviews.' },
]

export const RESTAURANTS = [
  {
    id: 'rest-via-carota', label: 'Via Carota',
    meta: { neighborhood: 'West Village', cuisine: 'italian', price: 3 },
    detail: 'Rustic Italian, no reservations, legendary svizzerina.',
    recommended_by: [
      { source: 'friend-dana', quote: 'Best cacio e pepe of my life. Go at 4pm or suffer.' },
      { source: 'src-eater' },
      { source: 'src-nyt' },
    ],
  },
  {
    id: 'rest-lilia', label: 'Lilia',
    meta: { neighborhood: 'Williamsburg', cuisine: 'italian', price: 3 },
    detail: "Missy Robbins' pasta temple in a converted auto shop.",
    recommended_by: [
      { source: 'friend-dana', quote: 'The mafaldini alone is worth the wait.' },
      { source: 'friend-omer', quote: '9.4/10 in my spreadsheet. Highest pasta score ever.' },
      { source: 'src-michelin' },
    ],
  },
  {
    id: 'rest-raku', label: 'Raku',
    meta: { neighborhood: 'East Village', cuisine: 'japanese', price: 2 },
    detail: 'Tiny handmade-udon shop, cash friendly, zero fuss.',
    recommended_by: [
      { source: 'friend-maya', quote: 'Quiet, cheap, perfect udon. My favorite spot in the city.' },
    ],
  },
  {
    id: 'rest-le-bernardin', label: 'Le Bernardin',
    meta: { neighborhood: 'Midtown', cuisine: 'french-seafood', price: 4 },
    detail: "Eric Ripert's three-Michelin-star seafood institution.",
    recommended_by: [{ source: 'src-michelin' }, { source: 'src-nyt' }],
  },
  {
    id: 'rest-katzs', label: "Katz's Delicatessen",
    meta: { neighborhood: 'Lower East Side', cuisine: 'deli', price: 2 },
    detail: 'The pastrami sandwich. Since 1888.',
    recommended_by: [{ source: 'src-google' }, { source: 'src-eater' }],
  },
  {
    id: 'rest-superiority-burger', label: 'Superiority Burger',
    meta: { neighborhood: 'East Village', cuisine: 'vegetarian', price: 1 },
    detail: 'Cult vegetarian burgers and gelato.',
    recommended_by: [{ source: 'src-eater' }],
  },
  {
    id: 'rest-cosme', label: 'Cosme',
    meta: { neighborhood: 'Flatiron', cuisine: 'mexican', price: 4 },
    detail: 'Modern Mexican; the duck carnitas and corn husk meringue.',
    recommended_by: [{ source: 'src-nyt' }, { source: 'src-michelin' }],
  },
  {
    id: 'rest-joes-pizza', label: "Joe's Pizza",
    meta: { neighborhood: 'Greenwich Village', cuisine: 'pizza', price: 1 },
    detail: 'The classic NY slice, open till 4am.',
    recommended_by: [{ source: 'src-google' }],
  },
]

export const HOTELS = [
  {
    id: 'hotel-bowery', label: 'The Bowery Hotel',
    meta: { neighborhood: 'East Village', price: 4 },
    detail: 'Old-world lobby, terrace bar, downtown icon.',
    recommended_by: [
      { source: 'friend-maya', quote: 'Worth it just for the lobby fireplace.' },
      { source: 'src-nyt' },
    ],
  },
  {
    id: 'hotel-ace', label: 'Ace Hotel',
    meta: { neighborhood: 'NoMad', price: 3 },
    detail: 'Lobby full of laptops by day, DJs by night.',
    recommended_by: [
      { source: 'friend-omer', quote: 'Stayed twice for work. Great coffee downstairs.' },
    ],
  },
  {
    id: 'hotel-wythe', label: 'Wythe Hotel',
    meta: { neighborhood: 'Williamsburg', price: 3 },
    detail: 'Converted 1901 factory with Manhattan skyline views.',
    recommended_by: [{ source: 'src-eater' }],
  },
  {
    id: 'hotel-pod51', label: 'Pod 51',
    meta: { neighborhood: 'Midtown East', price: 1 },
    detail: 'Tiny smart rooms, unbeatable price, rooftop deck.',
    recommended_by: [{ source: 'src-google' }],
  },
]

const sourceNode = (id) => {
  const f = FRIENDS.find((x) => x.id === id)
  if (f) return { ...f, type: 'person.friend' }
  const p = PUBLICATIONS.find((x) => x.id === id)
  return { ...p, type: 'source.publication' }
}

// Builds the update_graph payload that adds a set of places (with their
// sources) around a topic hub. Used by the simulated demo script; live voice
// produces equivalent payloads through tool calls.
export function buildPlacesOps({ places, placeType, topicId, topicLabel }) {
  const nodes = [{ id: topicId, type: 'topic', label: topicLabel, detail: 'Conversation topic' }]
  const edges = []
  const seenSources = new Set()
  for (const place of places) {
    nodes.push({ id: place.id, type: placeType, label: place.label, detail: place.detail, meta: place.meta })
    edges.push({ source: place.id, target: topicId, type: 'located_in' })
    for (const rec of place.recommended_by) {
      if (!seenSources.has(rec.source)) {
        seenSources.add(rec.source)
        nodes.push(sourceNode(rec.source))
      }
      edges.push({ source: rec.source, target: place.id, type: 'recommends', quote: rec.quote })
    }
  }
  return [
    { op: 'add_nodes', nodes },
    { op: 'add_edges', edges },
    { op: 'focus', node_ids: nodes.map((n) => n.id) },
  ]
}

export const FRIENDS_FILTER = (placeTypes = ['place.restaurant', 'place.hotel']) => ({
  op: 'apply_filter',
  filter: {
    description: 'friend recommendations only',
    keep_node_types: placeTypes,
    require_edge: { type: 'recommends', from_node_type: 'person.friend' },
  },
})

// The full dataset as JSON, embedded into the live voice session instructions.
export const DATASET_JSON = JSON.stringify(
  { friends: FRIENDS, publications: PUBLICATIONS, restaurants: RESTAURANTS, hotels: HOTELS },
  null,
  1,
)
