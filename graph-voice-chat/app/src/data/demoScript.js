import { RESTAURANTS, HOTELS, buildPlacesOps, FRIENDS_FILTER } from './mockData.js'

// The canonical demo, played by Simulated mode. Each step: user caption,
// spoken assistant line (Web Speech API), and an update_graph payload applied
// through the exact same store path as live tool calls.

export const DEMO_STEPS = [
  {
    user: 'Show me restaurant recommendations in New York.',
    assistant:
      "Here's what I've got in New York — eight spots worth knowing. The pink lines are recommendations from your friends: Dana swears by Via Carota and Lilia, and Maya's pick is a little udon shop called Raku. The rest come from Eater, the Times, Michelin and Google.",
    payload: {
      title: 'Restaurants in NYC',
      operations: buildPlacesOps({
        places: RESTAURANTS,
        placeType: 'place.restaurant',
        topicId: 'topic-nyc',
        topicLabel: 'New York',
      }),
    },
  },
  {
    user: 'Show me only the ones my friends recommended.',
    assistant:
      "Done — I've faded out five places. You're left with Via Carota and Lilia from Dana — Omer scored Lilia a nine point four — and Raku, Maya's favorite udon spot in the East Village.",
    payload: {
      title: 'Restaurants in NYC — friends only',
      operations: [
        FRIENDS_FILTER(['place.restaurant']),
        { op: 'highlight', node_ids: ['rest-via-carota', 'rest-lilia', 'rest-raku'] },
        { op: 'focus', node_ids: ['rest-via-carota', 'rest-lilia', 'rest-raku', 'friend-dana', 'friend-omer', 'friend-maya'] },
      ],
    },
  },
  {
    user: 'Which of those is cheapest?',
    assistant:
      "Raku — it's the most affordable of the three, around two dollar signs, and Maya says the handmade udon is the best in the city.",
    payload: {
      operations: [
        { op: 'highlight', node_ids: ['rest-raku'] },
        { op: 'focus', node_ids: ['rest-raku', 'friend-maya'] },
      ],
    },
  },
  {
    user: 'Okay, show everything again.',
    assistant: 'Back to the full picture — all eight spots are on the board.',
    payload: {
      title: 'Restaurants in NYC',
      operations: [{ op: 'clear_filter' }, { op: 'focus', node_ids: [] }],
    },
  },
  {
    user: 'What about hotels?',
    assistant:
      "Adding four — Maya loves The Bowery Hotel for the lobby alone, and Omer's stayed at the Ace twice. The Wythe and Pod fifty-one round it out from Eater and Google.",
    payload: {
      title: 'Restaurants & hotels in NYC',
      operations: buildPlacesOps({
        places: HOTELS,
        placeType: 'place.hotel',
        topicId: 'topic-nyc',
        topicLabel: 'New York',
      }).slice(0, 2).concat([{ op: 'focus', node_ids: HOTELS.map((h) => h.id) }]),
    },
  },
]
