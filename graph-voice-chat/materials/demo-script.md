# Canonical demo script

The exact sequence for live demos and for the prototype's Simulated mode. Each step lists the user utterance, the expected assistant speech (canned in simulated mode), and the expected graph effect.

## Step 1 — Bloom

**User:** "Show me restaurant recommendations in New York."

**Assistant (spoken):** "Here's what I've got in New York — eight spots worth knowing. The pink lines are recommendations from your friends: Dana swears by Via Carota and Lilia, and Maya's pick is a little udon shop called Raku. The rest come from Eater, the Times, Michelin and Google."

**Graph:** `New York` topic hub appears center; 8 restaurant nodes bloom around it (staggered entrance); friend nodes Dana/Omer/Maya and publication badges Eater NY / NYT Food / Michelin / Google Reviews attach with `recommends` edges; dashed `located_in` edges to the hub; title → "Restaurants in NYC"; camera fits all.

## Step 2 — Friends-only filter

**User:** "Show me only the ones my friends recommended."

**Assistant (spoken):** "Done — I've faded out five places. You're left with Via Carota and Lilia from Dana — Omer scored Lilia a nine-point-four — and Raku, Maya's favorite udon spot in the East Village."

**Graph:** friends-only filter applies; Le Bernardin, Katz's, Superiority Burger, Cosme and Joe's Pizza ghost to 12% opacity with labels hidden; publication badges connected only to ghosts dim; Dana, Omer, Maya glow; the three survivors pulse; layout re-settles; title → "Restaurants in NYC — friends only".

## Step 3 — Question without a filter

**User:** "Which of those is cheapest?"

**Assistant (spoken):** "Raku — it's the most affordable of the three, around two dollar signs, and Maya says the handmade udon is the best in the city."

**Graph:** no filter change; Raku pulses, camera nudges toward it; popover-worthy quote available on click.

## Step 4 — Restore

**User:** "Okay, show everything again."

**Assistant (spoken):** "Back to the full picture — all eight spots are on the board."

**Graph:** `clear_filter`; ghosts fade back in at their kept positions; title → "Restaurants in NYC".

## Step 5 (stretch) — Pivot to hotels

**User:** "What about hotels?"

**Assistant (spoken):** "Adding four — Maya loves The Bowery Hotel for the lobby alone, and Omer's stayed at the Ace twice. The Wythe and Pod 51 round it out from Eater and Google."

**Graph:** 4 amber hotel nodes join the same New York hub with their sources; camera focuses on the hotel cluster; restaurants remain.
