# backend/app/routers/trips.py
from __future__ import annotations

import math
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas import TripGenerateResponse, TripRequest
from app.services.google_places import search_places
from app.services.weather import get_weather_for_destination

router = APIRouter()

ATTRACTIONS_PER_DAY = 4
DEFAULT_RESTAURANT_LIMIT = 35
DEFAULT_HIGHLIGHT_LIMIT = 50
DEFAULT_HOTEL_LIMIT = 8
DEFAULT_NEIGHBORHOOD_LIMIT = 12


# -----------------------------
# Helpers: robust payload handling
# -----------------------------
def _ensure_trip_request(payload: Any) -> TripRequest:
    if isinstance(payload, TripRequest):
        return payload
    if isinstance(payload, dict):
        return TripRequest.model_validate(payload)
    return TripRequest.model_validate(payload)


def _norm_list(x: Any) -> list[str]:
    if not x:
        return []
    if isinstance(x, list):
        return [str(v).strip() for v in x if str(v).strip()]
    if isinstance(x, str):
        return [v.strip() for v in x.split(",") if v.strip()]
    return []


def _dietary_prefs_from_payload(payload: TripRequest) -> list[str]:
    preferences = payload.preferences or {}
    return [p.lower().strip() for p in _norm_list(preferences.get("dietary_preferences"))]


def _interests_from_payload(payload: TripRequest) -> list[str]:
    preferences = payload.preferences or {}
    return [p.lower().strip() for p in _norm_list(preferences.get("top_interests"))]


# -----------------------------
# Safe wrappers
# -----------------------------
def safe_search_places(query: str, limit: int = 8) -> list[dict[str, Any]]:
    try:
        return search_places(query, limit=limit) or []
    except Exception:
        return []


def safe_get_weather(destination: str) -> dict[str, Any] | None:
    try:
        return get_weather_for_destination(destination)
    except Exception:
        return None


# -----------------------------
# Query builder + fallbacks
# -----------------------------
def build_place_queries(payload: TripRequest | dict[str, Any]) -> dict[str, str]:
    """
    Works for both TripRequest and dict payloads.
    """
    if isinstance(payload, TripRequest):
        destination = payload.destination.strip()
        notes = (payload.notes or "").strip()
        must_see = ", ".join(payload.must_see or []).strip()
        dietary = _dietary_prefs_from_payload(payload)
        interests = _interests_from_payload(payload)
    else:
        destination = str(payload.get("destination", "")).strip()
        notes = str(payload.get("notes") or "").strip()
        must_see = ", ".join(payload.get("must_see") or []).strip()
        prefs = payload.get("preferences") or {}
        dietary = [p.lower().strip() for p in _norm_list(prefs.get("dietary_preferences"))]
        interests = [p.lower().strip() for p in _norm_list(prefs.get("top_interests"))]

    diet_hint = " " + " ".join([f"{d} friendly" for d in dietary]) if dietary else ""
    interest_hint = " " + " ".join(interests) if interests else ""
    must_see_hint = f" must see: {must_see}" if must_see else ""

    return {
        "restaurants": f"best restaurants{diet_hint} in {destination} {notes}".strip(),
        "hotels": f"best hotels in {destination} {notes}".strip(),
        "highlights": f"top attractions things to do in {destination} {interest_hint} {notes}{must_see_hint}".strip(),
        "neighborhoods": f"best neighborhoods to explore in {destination} {notes}".strip(),
    }


def build_restaurants_fallback(destination: str) -> list[dict[str, Any]]:
    return [{"name": f"Popular local restaurant in {destination}"}]


def build_hotels_fallback(destination: str) -> list[dict[str, Any]]:
    return [{"name": f"Well-rated hotel in {destination}"}]


def build_highlights_fallback(destination: str) -> list[dict[str, Any]]:
    return [{"name": f"Top attraction in {destination}"}]


def build_neighborhoods_fallback() -> list[str]:
    return ["Central"]


# -----------------------------
# Place field extraction
# -----------------------------
def _place_address(place: dict[str, Any] | None) -> str | None:
    if not place:
        return None
    return place.get("address") or place.get("formatted_address")


def _place_lat(place: dict[str, Any] | None) -> float | None:
    if not place:
        return None
    v = (
        place.get("lat")
        or place.get("latitude")
        or (place.get("geometry") or {}).get("location", {}).get("lat")
    )
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


def _place_lng(place: dict[str, Any] | None) -> float | None:
    if not place:
        return None
    v = (
        place.get("lng")
        or place.get("longitude")
        or (place.get("geometry") or {}).get("location", {}).get("lng")
    )
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


def _place_maps_url(place: dict[str, Any] | None) -> str | None:
    if not place:
        return None
    return place.get("google_maps_url") or place.get("url")


def _place_types(place: dict[str, Any] | None) -> set[str]:
    if not place:
        return set()
    raw = place.get("types") or place.get("place_types") or []
    if isinstance(raw, str):
        raw = [raw]
    return {str(t).lower() for t in raw if t}


def _place_text(place: dict[str, Any] | None) -> str:
    if not place:
        return ""
    parts = [
        str(place.get("name") or ""),
        str(place.get("summary") or ""),
        str(_place_address(place) or ""),
        " ".join(sorted(_place_types(place))),
    ]
    return " ".join(p for p in parts if p).lower()


def _place_line(place: dict[str, Any] | None) -> str:
    if not place:
        return "a local spot"
    name = place.get("name") or "a local spot"
    addr = _place_address(place)
    return f"{name} — {addr}" if addr else name


# -----------------------------
# Dietary scoring + filtering
# -----------------------------
DIET_KEYWORDS: dict[str, list[str]] = {
    "vegan": ["vegan", "plant-based", "plant based"],
    "vegetarian": ["vegetarian", "veggie"],
    "gluten-free": ["gluten-free", "gluten free", "gf"],
    "dairy-free": ["dairy-free", "dairy free", "lactose-free", "lactose free"],
    "halal": ["halal"],
    "kosher": ["kosher"],
    "pescatarian": ["pescatarian"],
}

VEGAN_AVOID_KEYWORDS = [
    "steak", "steakhouse", "bbq", "barbecue", "smokehouse",
    "butcher", "meat", "ribs", "rib", "burger", "wings",
    "seafood", "fish", "oyster", "lobster", "crab", "shrimp",
    "chicken", "bacon", "sausage",
]


def _rating(place: dict[str, Any]) -> float:
    try:
        return float(place.get("rating") or 0.0)
    except Exception:
        return 0.0


def _reviews(place: dict[str, Any]) -> float:
    v = place.get("user_ratings_total") or place.get("user_rating_count") or 0
    try:
        return float(v)
    except Exception:
        return 0.0


def restaurant_score(place: dict[str, Any], dietary_prefs: list[str]) -> float:
    score = _rating(place) * 2.0 + min(math.log1p(_reviews(place)), 10.0)
    txt = _place_text(place)

    for pref in dietary_prefs:
        keys = DIET_KEYWORDS.get(pref, [])
        if any(k in txt for k in keys):
            score += 4.0

    if "vegan" in dietary_prefs:
        has_vegan = any(k in txt for k in DIET_KEYWORDS["vegan"])
        if not has_vegan and any(k in txt for k in VEGAN_AVOID_KEYWORDS):
            score -= 6.0

    if any(k in txt for k in ["cafe", "coffee", "bakery", "breakfast", "brunch"]):
        score += 1.5

    return score


def attraction_score(place: dict[str, Any]) -> float:
    return _rating(place) * 2.0 + min(math.log1p(_reviews(place)), 10.0)


def filter_restaurants_for_diet(restaurants: list[dict[str, Any]], dietary_prefs: list[str]) -> list[dict[str, Any]]:
    if "vegan" not in dietary_prefs:
        return restaurants

    filtered: list[dict[str, Any]] = []
    for r in restaurants:
        txt = _place_text(r)
        has_vegan = any(k in txt for k in DIET_KEYWORDS["vegan"])
        looks_meaty = any(k in txt for k in VEGAN_AVOID_KEYWORDS)
        if looks_meaty and not has_vegan:
            continue
        filtered.append(r)

    return filtered if len(filtered) >= max(8, len(restaurants) // 3) else restaurants


def rank_restaurants(restaurants: list[dict[str, Any]], dietary_prefs: list[str]) -> list[dict[str, Any]]:
    r2 = filter_restaurants_for_diet(restaurants, dietary_prefs)
    return sorted(r2, key=lambda p: restaurant_score(p, dietary_prefs), reverse=True)


def rank_attractions(highlights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(highlights, key=attraction_score, reverse=True)


# -----------------------------
# Geo clustering helpers
# -----------------------------
def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _kmeans_centers(points: list[tuple[float, float]], k: int) -> list[tuple[float, float]]:
    pts = sorted(points, key=lambda x: (x[0], x[1]))
    if not pts:
        return []
    if k <= 1:
        return [pts[len(pts) // 2]]
    idxs = [round(i * (len(pts) - 1) / (k - 1)) for i in range(k)]
    return [pts[i] for i in idxs]


def kmeans_cluster_indices(points: list[tuple[float, float]], k: int, iters: int = 8) -> list[int]:
    if not points:
        return []
    k = max(1, min(k, len(points)))
    centers = _kmeans_centers(points, k)

    def dist2(p: tuple[float, float], c: tuple[float, float]) -> float:
        lat, lng = p
        clat, clng = c
        scale = math.cos(math.radians((lat + clat) / 2)) or 1.0
        dx = (lng - clng) * scale
        dy = (lat - clat)
        return dx * dx + dy * dy

    assignments = [0] * len(points)
    for _ in range(iters):
        for i, p in enumerate(points):
            best_j = 0
            best_d = dist2(p, centers[0])
            for j in range(1, len(centers)):
                d = dist2(p, centers[j])
                if d < best_d:
                    best_d = d
                    best_j = j
            assignments[i] = best_j

        sums = [(0.0, 0.0, 0) for _ in centers]
        for i, a in enumerate(assignments):
            lat, lng = points[i]
            ls, gs, cnt = sums[a]
            sums[a] = (ls + lat, gs + lng, cnt + 1)

        new_centers: list[tuple[float, float]] = []
        for j, (ls, gs, cnt) in enumerate(sums):
            if cnt == 0:
                new_centers.append(points[j % len(points)])
            else:
                new_centers.append((ls / cnt, gs / cnt))
        centers = new_centers

    return assignments


def cluster_places_by_day(highlights: list[dict[str, Any]], days: int) -> list[list[dict[str, Any]]]:
    usable: list[dict[str, Any]] = []
    unusable: list[dict[str, Any]] = []
    for h in highlights:
        if _place_lat(h) is not None and _place_lng(h) is not None:
            usable.append(h)
        else:
            unusable.append(h)

    if len(usable) < 4 or days <= 1:
        out = [[] for _ in range(days)]
        all_h = usable + unusable
        for i, h in enumerate(all_h):
            out[i % days].append(h)
        return out

    points = [(_place_lat(h), _place_lng(h)) for h in usable]  # type: ignore[arg-type]
    k = min(days, max(1, len(usable) // max(2, ATTRACTIONS_PER_DAY)))
    assigns = kmeans_cluster_indices(points, k=k, iters=8)

    clusters: list[list[dict[str, Any]]] = [[] for _ in range(k)]
    for h, a in zip(usable, assigns):
        clusters[a].append(h)

    clusters = [rank_attractions(c) for c in clusters]

    day_clusters: list[list[dict[str, Any]]] = [[] for _ in range(days)]
    for d in range(days):
        day_clusters[d] = clusters[d % k][:]

    for i, h in enumerate(unusable):
        day_clusters[i % days].append(h)

    return day_clusters


def cluster_center(cluster: list[dict[str, Any]]) -> tuple[float, float] | None:
    coords = [(_place_lat(p), _place_lng(p)) for p in cluster]
    coords = [(lat, lng) for lat, lng in coords if lat is not None and lng is not None]  # type: ignore[misc]
    if not coords:
        return None
    lat = sum(c[0] for c in coords) / len(coords)
    lng = sum(c[1] for c in coords) / len(coords)
    return (lat, lng)


# -----------------------------
# Itinerary building
# -----------------------------
def _trip_days(start_date: str, end_date: str) -> int:
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    return max(1, (e - s).days + 1)


def _rotate_neighborhoods(neighborhoods: list[str], days: int) -> list[str]:
    if not neighborhoods:
        return ["Central"] * days
    seen: set[str] = set()
    uniq: list[str] = []
    for n in neighborhoods:
        n2 = (n or "").strip()
        if not n2 or n2 in seen:
            continue
        seen.add(n2)
        uniq.append(n2)
    if not uniq:
        return ["Central"] * days
    return [uniq[i % len(uniq)] for i in range(days)]


def _pick_diverse_attractions_for_day(
    day_candidates: list[dict[str, Any]],
    used_sites: set[str],
    count: int = ATTRACTIONS_PER_DAY,
) -> list[dict[str, Any] | None]:
    picked: list[dict[str, Any]] = []
    day_types: set[str] = set()

    for it in day_candidates:
        nm = (it.get("name") or "").strip()
        if not nm or nm in used_sites:
            continue
        types = _place_types(it)
        if types and (types & day_types):
            continue
        picked.append(it)
        used_sites.add(nm)
        day_types |= types
        if len(picked) >= count:
            break

    if len(picked) < count:
        for it in day_candidates:
            nm = (it.get("name") or "").strip()
            if not nm or nm in used_sites:
                continue
            picked.append(it)
            used_sites.add(nm)
            if len(picked) >= count:
                break

    if len(picked) < count:
        for it in day_candidates:
            if len(picked) >= count:
                break
            picked.append(it)

    while len(picked) < count:
        picked.append(None)

    return picked[:count]


def _meal_kind(place: dict[str, Any] | None) -> str:
    if not place:
        return "unknown"
    txt = _place_text(place)
    if any(k in txt for k in ["cafe", "coffee", "bakery", "breakfast", "brunch"]):
        return "breakfast"
    return "restaurant"


def pick_nearby_meals_for_day(
    center: tuple[float, float] | None,
    restaurants_ranked: list[dict[str, Any]],
    used_restaurants: set[str],
    dietary_prefs: list[str],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    scored: list[tuple[float, float, dict[str, Any]]] = []
    for r in restaurants_ranked:
        nm = (r.get("name") or "").strip()
        if not nm or nm in used_restaurants:
            continue
        lat = _place_lat(r)
        lng = _place_lng(r)
        dist = 0.0
        if center and lat is not None and lng is not None:
            dist = haversine_m(center[0], center[1], lat, lng)
        scored.append((restaurant_score(r, dietary_prefs), -dist, r))

    if not scored:
        for r in restaurants_ranked:
            nm = (r.get("name") or "").strip()
            if not nm:
                continue
            lat = _place_lat(r)
            lng = _place_lng(r)
            dist = 0.0
            if center and lat is not None and lng is not None:
                dist = haversine_m(center[0], center[1], lat, lng)
            scored.append((restaurant_score(r, dietary_prefs), -dist, r))

    scored.sort(reverse=True)

    kinds: set[str] = set()

    def pick_one(prefer: str | None) -> dict[str, Any] | None:
        for _, __, r in scored:
            nm = (r.get("name") or "").strip()
            if not nm or nm in used_restaurants:
                continue
            kind = _meal_kind(r)
            if prefer and kind != prefer:
                continue
            if kind != "unknown" and kind in kinds:
                continue
            used_restaurants.add(nm)
            kinds.add(kind)
            return r
        return None

    breakfast = pick_one("breakfast") or pick_one(None)
    lunch = pick_one(None)
    dinner = pick_one(None)

    if breakfast is None and scored:
        breakfast = scored[0][2]
    if lunch is None and len(scored) > 1:
        lunch = scored[1][2]
    if dinner is None and len(scored) > 2:
        dinner = scored[2][2]

    return breakfast, lunch, dinner


def _blurb(place: dict[str, Any] | None, kind: str) -> str:
    if not place:
        return "A solid pick based on reviews and location."
    name = place.get("name") or "This spot"
    rating = place.get("rating")
    cnt = place.get("user_ratings_total") or place.get("user_rating_count")
    rating_part = ""
    if rating is not None:
        rating_part = f"Rated {rating}"
        if cnt:
            rating_part += f" ({cnt} reviews)"
        rating_part += ". "
    if kind in {"breakfast", "lunch"}:
        return f"{rating_part}{name} is convenient and well-reviewed—perfect for refueling between stops."
    if kind == "dinner":
        return f"{rating_part}{name} is a standout dinner option—great reviews and a strong local feel."
    if kind == "site":
        return f"{rating_part}{name} is a signature stop worth prioritizing for the experience."
    return f"{rating_part}{name} is a highly rated option."


def _push_place(out: list[dict[str, Any]], *, day: int, category: str, place: dict[str, Any] | None) -> None:
    if not place:
        return
    lat = _place_lat(place)
    lng = _place_lng(place)
    if lat is None or lng is None:
        return
    out.append(
        {
            "day": day,
            "category": category,
            "name": place.get("name"),
            "address": _place_address(place),
            "lat": lat,
            "lng": lng,
            "google_maps_url": _place_maps_url(place),
            "rating": place.get("rating"),
            "user_rating_count": place.get("user_ratings_total") or place.get("user_rating_count"),
        }
    )


def build_rich_days_and_places(
    *,
    destination: str,
    start_date: str,
    end_date: str,
    restaurants: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
    neighborhoods: list[str],
    dietary_prefs: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    days = _trip_days(start_date, end_date)

    restaurants_ranked = rank_restaurants(restaurants, dietary_prefs)
    highlights_ranked = rank_attractions(highlights)

    day_clusters = cluster_places_by_day(highlights_ranked, days=days)
    neighborhood_plan = _rotate_neighborhoods(neighborhoods, days)

    used_restaurants: set[str] = set()
    used_sites: set[str] = set()

    itinerary: list[dict[str, Any]] = []
    places: list[dict[str, Any]] = []

    for i in range(days):
        day_num = i + 1
        day_cluster = day_clusters[i]
        center = cluster_center(day_cluster)

        chosen_sites = _pick_diverse_attractions_for_day(day_cluster, used_sites, count=ATTRACTIONS_PER_DAY)
        breakfast, lunch, dinner = pick_nearby_meals_for_day(
            center=center,
            restaurants_ranked=restaurants_ranked,
            used_restaurants=used_restaurants,
            dietary_prefs=dietary_prefs,
        )

        _push_place(places, day=day_num, category="breakfast", place=breakfast)
        _push_place(places, day=day_num, category="lunch", place=lunch)
        _push_place(places, day=day_num, category="dinner", place=dinner)

        for s in chosen_sites:
            _push_place(places, day=day_num, category="attraction", place=s)

        hood = neighborhood_plan[i] if i < len(neighborhood_plan) else _infer_neighborhood_from_address(chosen_sites[0] or dinner)
        featured_site = next((s for s in chosen_sites if s), None)

        stops: list[dict[str, Any]] = [{"time_block": "Breakfast", "place": _place_line(breakfast)}]
        time_blocks = ["Morning", "Late Morning", "Afternoon", "Late Afternoon"]
        for tb, site in zip(time_blocks, chosen_sites):
            stops.append({"time_block": tb, "place": _place_line(site)})
        stops.extend([{"time_block": "Lunch", "place": _place_line(lunch)}, {"time_block": "Dinner", "place": _place_line(dinner)}])

        itinerary.append(
            {
                "day": day_num,
                "title": f"Day {day_num} in {destination}",
                "meals": {
                    "breakfast": {"place": _place_line(breakfast), "blurb": _blurb(breakfast, "breakfast")},
                    "lunch": {"place": _place_line(lunch), "blurb": _blurb(lunch, "lunch")},
                    "dinner": {"place": _place_line(dinner), "blurb": _blurb(dinner, "dinner")},
                },
                "stops": stops,
                "spotlight": {
                    "neighborhood": {
                        "name": hood,
                        "blurb": f"Today is centered around **{hood}**—your attractions are clustered to minimize transit.",
                    },
                    "restaurant": {
                        "name": (dinner or lunch or breakfast or {}).get("name"),
                        "google_maps_url": _place_maps_url(dinner or lunch or breakfast),
                        "blurb": _blurb(dinner or lunch or breakfast, "dinner"),
                    },
                    "site": {
                        "name": (featured_site or {}).get("name"),
                        "google_maps_url": _place_maps_url(featured_site),
                        "blurb": _blurb(featured_site, "site"),
                    },
                },
                "notes": [],
            }
        )

    # De-dupe pins by (day, category, name)
    seen = set()
    deduped: list[dict[str, Any]] = []
    for p in places:
        key = (p.get("day"), p.get("category"), p.get("name"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    return itinerary, deduped


# -----------------------------
# Route: POST /api/trips/generate
# -----------------------------
@router.post("/generate", response_model=TripGenerateResponse)
def generate_trip(payload: TripRequest) -> TripGenerateResponse:
    try:
        payload = _ensure_trip_request(payload)

        queries = build_place_queries(payload)

        dietary_prefs = _dietary_prefs_from_payload(payload)

        restaurants = safe_search_places(queries["restaurants"], limit=DEFAULT_RESTAURANT_LIMIT)
        hotels = safe_search_places(queries["hotels"], limit=DEFAULT_HOTEL_LIMIT)
        highlights = safe_search_places(queries["highlights"], limit=DEFAULT_HIGHLIGHT_LIMIT)
        neighborhood_results = safe_search_places(queries["neighborhoods"], limit=DEFAULT_NEIGHBORHOOD_LIMIT)
        weather = safe_get_weather(payload.destination)

        if not restaurants:
            restaurants = build_restaurants_fallback(payload.destination)
        if not hotels:
            hotels = build_hotels_fallback(payload.destination)
        if not highlights:
            highlights = build_highlights_fallback(payload.destination)

        neighborhoods = [str(item.get("name")).strip() for item in neighborhood_results if item.get("name")]
        neighborhoods = [n for n in neighborhoods if n] or build_neighborhoods_fallback()

        itinerary, places = build_rich_days_and_places(
            destination=payload.destination,
            start_date=payload.start_date,
            end_date=payload.end_date,
            restaurants=restaurants,
            highlights=highlights,
            neighborhoods=neighborhoods,
            dietary_prefs=dietary_prefs,
        )

        # legacy pins (keep for backward compatibility)
        map_points: list[dict[str, Any]] = []
        for category, items in [("restaurant", restaurants), ("hotel", hotels), ("highlight", highlights)]:
            for item in items:
                lat = _place_lat(item)
                lng = _place_lng(item)
                if lat is None or lng is None:
                    continue
                map_points.append({"name": item.get("name"), "lat": lat, "lng": lng, "category": category})

        summary = payload.notes or f"Trip to {payload.destination}"
        tips = [
            "Days are clustered by location to reduce transit time.",
            "Meals are selected near each day’s cluster and boosted for dietary preferences.",
            "Swap indoor/outdoor stops if weather shifts.",
        ]

        return TripGenerateResponse(
            destination=payload.destination,
            summary=summary,
            weather=weather,
            neighborhoods=neighborhoods,
            restaurants=restaurants,
            hotels=hotels,
            highlights=highlights,
            map_points=map_points,
            itinerary=itinerary,
            tips=tips,
            places=places,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))