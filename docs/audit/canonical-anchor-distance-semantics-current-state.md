# Canonical Shrine Anchor — distanceM Current-State Audit

## Status

- Status: `ASSESSMENT_ONLY`
- Recorded at: `2026-09-23`
- Subject: `A-3 distanceM semantics`
- Scope in this document: current producer / consumer trace only
- A-3 Mother Ship decision: `RESOLVED_PROXIMITY`
- Production write: `NONE`
- Base Seed write: `NONE`
- Runtime behavior change: `NONE`
- Position Contract change: `NONE`
- Migration Gate selection: `NONE`

This audit answers:

```text
1. What currently produces Shrine recommendation distance_m?
2. Which current consumers use it?
3. Is the same field already a route distance?
```

It does not yet decide whether product-facing distance semantics should be
`PROXIMITY` or `NAVIGATION`.

---

## 1. Executive Finding

For the main Shrine recommendation / Compass path:

```text
distance_m
= straight-line great-circle distance
  from runtime user origin
  to Shrine.latitude / Shrine.longitude
```

It is not a route distance.

The current value participates in:

```text
- candidate ordering before pool truncation
- Recommendation score
- final recommendation ordering / distance override
- Compass 15 / 30 / 60 km eligibility stages
- user-facing card display
- user-facing recommendation copy
- observation / analytics payloads
```

There is a separate route subsystem that also uses the field name `distance_m`, but
its semantics differ:

```text
route API distance_m
= route-provider route distance when OSRM succeeds

route_service DummyAdapter distance_m
= straight-line fallback leg distance
```

Therefore the repository currently contains multiple `distance_m` namespaces.
The recommendation `distance_m` must not be treated as proven travel distance merely
because route responses use the same key name.

---

## 2. Primary Producer — Concierge / Compass Recommendation Path

### 2.1 Producer

File:

`backend/temples/services/concierge_chat_candidates.py`

Function:

`_distance_m(lat1, lng1, lat2, lng2)`

Current implementation uses a Haversine great-circle calculation with earth radius
6,371,000 m.

The candidate builder calls:

```text
_distance_m(
  runtime origin lat/lng,
  Shrine.latitude,
  Shrine.longitude
)
```

and stores:

```text
candidate["lat"]        = Shrine.latitude
candidate["lng"]        = Shrine.longitude
candidate["distance_m"] = computed Haversine distance
```

Therefore:

```text
RECOMMENDATION_DISTANCE_PRODUCER
= USER_ORIGIN -> CURRENT_SHRINE_STORED_COORDINATE

PATH_TYPE
= STRAIGHT_LINE / GREAT_CIRCLE

ROUTE_GRAPH_USED
= NO
```

The same candidate builder requires Shrine latitude / longitude to exist and currently
excludes empty address rows.

### 2.2 Current upstream coordinate semantics

The ACTIVE Position Contract currently defines:

```text
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor
```

Therefore the current straight-line distance is presently measured to a coordinate
whose declared semantic role is Visitor / Navigation Anchor.

If that stored coordinate meaning changes later, the numeric producer automatically
changes meaning without changing this Haversine function.

---

## 3. Other Shrine / Nearby Producers

### 3.1 nearest_queryset / nearest_shrines

File:

`backend/temples/queries.py`

Current branches:

```text
PostGIS:
  ST_DistanceSphere(location, origin)

NoGIS PostgreSQL:
  Haversine over Shrine.latitude / longitude

SQLite fallback:
  Python Haversine over Shrine.latitude / longitude
```

These producers also use straight-line / spherical proximity semantics rather than a
road / walking route network.

The current Production audit previously recorded `USE_GIS = FALSE`, so Production's
relevant non-GIS branch uses numeric latitude / longitude rather than the stale
`location` field.

### 3.2 Places nearby search

File:

`backend/temples/api/views/search.py`

When upstream results do not already contain `distance_m`, the endpoint computes:

```text
_haversine_m(user lat/lng, result lat/lng)
```

and sorts results ascending by that value.

This is also straight-line proximity.

### 3.3 External Places candidates

File:

`backend/temples/llm/tools/places_search.py`

Google Places-style candidate coordinates are converted into:

```text
distance_m = Haversine(user origin, place coordinate)
```

This path is not Shrine model coordinate authority, but it confirms that the older
LLM plan path also treats `distance_m` as straight-line proximity.

---

## 4. Consumer Inventory — Candidate Retrieval

### C1. Pre-truncation candidate sort

File:

`backend/temples/services/concierge_chat_candidates.py`

When user origin exists, candidates are sorted:

```text
1. distance_m ascending
2. popular_score descending
3. name
```

before the candidate pool is truncated.

Result:

```text
distance_m
= candidate-retrieval signal
```

It can affect which Shrines survive into the downstream recommendation pool.

This means distance is not merely display metadata.

---

## 5. Consumer Inventory — Recommendation Scoring

### C2. Distance decay

File:

`backend/temples/services/concierge_chat_ranking.py`

Current formula:

```text
score_distance
= exp(-distance_m / 2500.0)
```

The distance score contributes to the internal ranked score:

```text
_score_total
includes
score_distance * w4
```

Result:

```text
distance_m
= ranking signal
```

A change in Shrine coordinate semantics therefore changes recommendation ranking even
if no scoring code changes.

---

## 6. Consumer Inventory — Final Recommendation Ordering

### C3. Normal recommendation ordering

File:

`backend/temples/services/concierge_chat.py`

Normal ordering uses:

```text
1. ranked score descending
2. distance_m ascending
3. name
```

Distance is therefore an explicit tie-break / secondary ordering key.

### C4. `sort_distance` override

The same file activates `distance_mode` when:

```text
"sort_distance" in sort_tags
```

The trigger vocabulary includes user requests such as:

```text
近い
近く
徒歩
できるだけ近
最寄り
距離優先
```

In that mode, candidates with established Primary-tier recommendation meaning remain
ahead of candidates without it, and `distance_m` sorts inside the tier.

Result:

```text
distance_m
= direct response to user intent such as "近い" / "徒歩" / "最寄り"
```

This is a stronger user-facing semantic dependency than a passive proximity signal.

---

## 7. Consumer Inventory — Compass Geographic Boundary

### C5. Compass 15 / 30 / 60 km stage

File:

`backend/temples/services/compass_recommendation_orchestrator.py`

After direction filtering, Compass applies:

```text
Stage 1 = <= 15 km
Stage 2 = <= 30 km
Stage 3 = <= 60 km
```

using candidate `distance_m`.

A missing / invalid distance excludes that Shrine from all stages.

Result:

```text
distance_m
= Compass eligibility boundary
```

The source value is still straight-line Haversine distance to the stored Shrine
coordinate.

---

## 8. Consumer Inventory — User-facing UI

### C6. ShrineCard

File:

`apps/web/src/components/shrines/ShrineCard.tsx`

The component formats and displays `distanceM` directly alongside rating.

There is no route-distance label attached to the value.

### C7. ShrineCardLite

File:

`apps/web/src/components/shrines/ShrineCardLite.tsx`

Displays:

```text
{distanceM}m
```

when numeric.

### C8. ShrineCardCompact

File:

`apps/web/src/components/shrines/ShrineCardCompact.tsx`

Default row behavior:

```text
address present
-> display address

address absent
-> display formatted distance
```

Therefore distance may be visually suppressed in ordinary Compact cards when address
is present.

### C9. Compass recommendation cards

File:

`apps/web/src/features/compass/components/CompassRecommendationsSection.tsx`

Compass explicitly surfaces the existing recommendation distance via:

```text
distanceLabel = "約" + formatDistance(distance_m)
```

even though the Compact card's ordinary address-vs-distance row would otherwise hide
it.

Result:

```text
Compass UI visibly presents straight-line recommendation distance
as an approximate distance value.
```

---

## 9. Consumer Inventory — User-facing Narrative

### C10. Recommendation reason narrative

File:

`apps/web/src/lib/concierge/buildReasonNarrative.ts`

Current generated copy includes phrases such as:

```text
"{distance}圏内で、実際に向かいやすい条件もあります。"

"{distance}圏内で、落ち着いて向かいやすい条件もあります。"

"今回はまず動きやすさを優先して、この神社が候補に入っています。"

"無理なく足を運びやすい条件もあります。"
```

The producer is still straight-line Haversine distance.

Therefore current presentation already interprets proximity as a practical
visitability / ease-of-going signal.

This is important for A-3:

```text
PRODUCER SEMANTICS
= straight-line proximity

SOME COPY SEMANTICS
= practical ease of getting there
```

Those are related, but they are not mathematically identical.

This audit records the mismatch; it does not resolve it.

---

## 10. Consumer Inventory — Secondary / Legacy Plan Path

### C11. Legacy LLM plan orchestrator

Files:

- `backend/temples/llm/tools/db_search.py`
- `backend/temples/llm/tools/places_search.py`
- `backend/temples/llm/tools/orchestrator.py`

The DB / Places tools calculate or expose `distance_m`, sort nearest-first, and the
orchestrator:

```text
sorts candidates by distance_m
picks nearest candidates
reason = "現在地から近いため。"
duration_min = rough_route(distance_m, transport)
```

The `rough_route` duration is derived from straight-line distance by a speed
assumption.

This is not equivalent to a route-provider travel duration.

---

## 11. Separate Namespace — Route distance_m

### 11.1 OSRM route endpoint

File:

`backend/temples/api/views/route.py`

When a route provider returns a route:

```text
distance_m = route["distance"]
duration_s = route["duration"]
geometry   = route["geometry"]
```

This is route-network output and has different semantics from recommendation
`distance_m`.

### 11.2 Route service fallback

File:

`backend/temples/route_service.py`

The DummyAdapter uses Haversine between route leg points and estimates duration from
a fixed speed.

Therefore even within the route subsystem, `distance_m` can mean:

```text
provider route distance
or
fallback straight-line leg distance
```

depending on adapter.

### 11.3 Naming collision

The shared key name does not imply a shared semantic contract.

```text
recommendation distance_m
!=
OSRM route distance_m
```

A-3 must therefore decide the recommendation / product distance meaning explicitly
instead of inheriting route semantics from the field name.

---

## 12. Non-behavioral Consumers

The following paths also retain / expose distance data but do not independently define
its meaning.

Examples:

```text
backend/temples/api/serializers/shrine.py
  normalizes d_m / distance_m / distance into numeric and text fields

backend/temples/services/concierge_observability.py
backend/temples/services/concierge_chat_observation.py
  record distance-related values for observation / analytics
```

These are propagation / observation consumers rather than primary semantic producers.

---

## 13. Current Producer / Consumer Matrix

| Surface | Producer / consumer role | Current semantics |
| --- | --- | --- |
| Concierge candidate generation | Producer | Haversine origin -> Shrine.latitude/longitude |
| nearest query | Producer | spherical / Haversine proximity |
| Places nearby | Producer | Haversine origin -> place coordinate |
| Candidate pre-sort | Consumer | nearer candidate preferred before truncation |
| Recommendation scoring | Consumer | exponential distance decay |
| Recommendation final sort | Consumer | tie-break / secondary ordering |
| `sort_distance` | Consumer | explicit "near / walking / nearest" user intent |
| Compass distance stage | Consumer | hard 15/30/60 km eligibility |
| Shrine cards | Consumer | displayed numeric distance |
| Compass cards | Consumer | displayed as "約..." |
| Recommendation narrative | Consumer | interpreted as easier / practical to visit |
| Legacy plan | Consumer | nearest-first + rough duration derivation |
| Route API | Separate producer | route-provider distance |
| Route fallback | Separate producer | Haversine route-leg fallback |

---

## 14. A-3 Evidence State After Current-state Trace

This audit does not select A-3, but narrows the decision.

```text
FACT-1
Main recommendation distance_m is straight-line proximity.

FACT-2
It is behaviorally significant before ranking, during scoring, final ordering, and
Compass eligibility.

FACT-3
It is surfaced to users.

FACT-4
Some current copy describes it as visitability / ease-of-going.

FACT-5
Actual route-provider distance exists separately and is not the recommendation
distance_m producer.

FACT-6
Changing Shrine.latitude / longitude semantics would automatically alter all
recommendation distance consumers.
```

Therefore the remaining Mother Ship question is no longer:

```text
"What does the code calculate?"
```

That is established.

The remaining question is:

```text
"What product meaning should straight-line recommendation distance be allowed to
represent after Canonical / Navigation Anchor semantics are decided?"
```

---

## 15. Required Statements

```text
1. No Production data was changed.
2. No Base Seed data was changed.
3. No runtime code was changed.
4. No active Contract was changed.
5. The initial current-state trace did not itself decide A-3; Mother Ship decision is recorded in §16.
6. Recommendation distance_m is not a route-provider distance.
7. Route distance_m and recommendation distance_m are separate semantic namespaces.
8. No Migration Gate option was selected.
```


---

## 16. Mother Ship Decision — A-3

After the current-state trace, Mother Ship resolved the product meaning of recommendation `distance_m`.

```text
A-3_DISTANCE_SEMANTICS
= PROXIMITY

CALCULATION
= STRAIGHT_LINE / GREAT_CIRCLE

PRODUCT_MEANING
= GEOGRAPHIC CLOSENESS

NAVIGATION_PROMISE
= NO

WALKING_DISTANCE_PROMISE
= NO

ROUTE_DISTANCE_PROMISE
= NO

CANONICAL_ANCHOR_COMPATIBLE
= YES, AS PROXIMITY

NAVIGATION_ANCHOR_REQUIRED_FOR_ROUTE
= YES
```

The canonical meaning is therefore:

```text
recommendation.distance_m
= straight-line geographic proximity between the runtime origin and the selected
  Shrine reference point used by Recommendation
```

It may be used to express that a Shrine is geographically nearer or farther within the
Recommendation context.

It must not be represented as:

```text
- walking route distance
- road-network distance
- remaining travel distance
- arrival distance
- route-provider distance
```

Those meanings belong to a separate navigation / route-distance concern.

### 16.1 Canonical / Navigation responsibility split

If a future Migration Gate adopts a Canonical Shrine Anchor, recommendation proximity
may be computed to that Canonical point without changing the A-3 meaning:

```text
user origin -> Canonical Shrine Anchor
= geographic proximity
```

Route guidance remains separate:

```text
user origin -> Navigation Anchor -> route provider
= navigation / route distance
```

Therefore:

```text
PROXIMITY_DISTANCE
!=
NAVIGATION_DISTANCE
```

### 16.2 Existing copy debt

The current producer computes proximity, while some current user-facing copy interprets
the value as practical ease of travel.

Examples already identified by this audit include wording equivalent to:

```text
- 実際に向かいやすい
- 動きやすさを優先
- 無理なく足を運びやすい
```

These phrases are stronger than the adopted A-3 Contract meaning because straight-line
proximity does not prove route accessibility.

This decision does not modify runtime copy.
It records the following follow-up debt:

```text
DISTANCE_COPY_ALIGNMENT_DEBT = OPEN
```

Future copy should distinguish proximity language from route / accessibility claims.

### 16.3 Existing sort-trigger debt

The current `sort_distance` trigger vocabulary includes terms such as:

```text
近い
近く
徒歩
できるだけ近
最寄り
距離優先
```

The adopted proximity semantics directly support proximity-oriented terms such as:

```text
近い / 近く / 距離優先
```

but terms such as `徒歩` and potentially `最寄り` can imply route / access semantics
that the Haversine value does not prove.

No runtime trigger is changed by this decision.
The mismatch is recorded as:

```text
DISTANCE_TRIGGER_ALIGNMENT_DEBT = OPEN
```

### 16.4 A-3 resolution

```text
A-3 = RESOLVED

RECOMMENDATION_DISTANCE_SEMANTICS
= PROXIMITY

ROUTE_DISTANCE_SEMANTICS
= SEPARATE

DISTANCE_COPY_ALIGNMENT_DEBT
= OPEN

DISTANCE_TRIGGER_ALIGNMENT_DEBT
= OPEN
```

This decision does not select the Canonical Shrine Anchor Migration Gate.
