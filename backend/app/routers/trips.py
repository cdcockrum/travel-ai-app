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
DEFAULT_RESTAURANT_LIMIT = 40
DEFAULT_HIGHLIGHT_LIMIT = 60
DEFAULT_HOTEL_LIMIT = 10
DEFAULT_NEIGHBORHOOD_LIMIT = 15


# -----------------------------
# Safe wrappers
# -----------------------------
def safe_search_places(query: str, limit: int = 8) -> list[dict[str, Any]]:
    try:
        results = search_places(query, limit=limit) or []
        return [r for r in results if isinstance(r, dict)]
    except Exception:
        return []


def safe_get_weather(destination: str) -> dict[str, Any] | None:
    try:
        return get_weather_for_destination(destination)
    except Exception:
        return None


# -----------------------------
# Payload helpers
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
# Places normalization
# -----------------------------
def _is_resource_name(value: str) -> bool:
    v = (value or "").strip()
    return v.startswith("places/") or v.startswith("ChIJ")


def _place_name(place: dict[str, Any] | None) -> str | None:
    if not place:
        return None

    # Places API v1
    dn = place.get("displayName")
    if isinstance(dn, dict):
        t = dn.get("text")
        if isinstance(t, str) and t.strip():
            return t.strip()
    if isinstance(dn, str) and dn.strip():
        return dn.strip()

    # Older output (but ignore resource ids)
    v = place.get("name")
    if isinstance(v, str) and v.strip() and not _is_resource_name(v):
        return v.strip()

    # fallback
    t2 = place.get("title")
    if isinstance(t2, str) and t2.strip():
        return t2.strip()

    return None


def _place_address(place: dict[str, Any] | None) -> str | None:
    if not place:
        return None
    for k in ("address", "formatted_address", "formattedAddress"):
        v = place.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _place_rating(place: dict[str, Any] | None) -> float | None:
    if not place:
        return None
    v = place.get("rating")
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


def _place_user_rating_count(place: dict[str, Any] | None) -> int | None:
    if not place:
        return None
    v = (
        place.get("user_ratings_total")
        or place.get("user_rating_count")
        or place.get("userRatingCount")
    )
    try:
        return int(v) if v is not None else None
    except Exception:
        return None


def _place_lat(place: dict[str, Any] | None) -> float | None:
    if not place:
        return None
    v = (
        place.get("lat")
        or place.get("latitude")
        or (place.get("geometry") or {}).get("location", {}).get("lat")
        or (place.get("location") or {}).get("latitude")
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
        or (place.get("location") or {}).get("longitude")
    )
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


def _place_maps_url(place: dict[str, Any] | None) -> str | None:
    if not place:
        return None
    for k in ("google_maps_url", "url", "googleMapsUri"):
        v = place.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _place_types(place: dict[str, Any] | None) -> list[str]:
    if not place:
        return []
    raw = place.get("types") or place.get("place_types") or []
    if isinstance(raw, str):
        raw = [raw]
    if isinstance(raw, list):
        return [str(t) for t in raw if str(t)]
    return []


def _normalize_place(place: dict[str, Any]) -> dict[str, Any]:
    # keep raw first, then overwrite with normalized keys
    out = dict(place)
    out["name"] = _place_name(place)
    out["address"] = _place_address(place)
    out["rating"] = _place_rating(place)
    out["user_rating_count"] = _place_user_rating_count(place)
    out["types"] = _place_types(place)
    out["lat"] = _place_lat(place)
    out["lng"] = _place_lng(place)
    out["google_maps_url"] = _place_maps_url(place)
    return out


def _has_real_name(place: dict[str, Any] | None) -> bool:
    return bool(_place_name(place))


def _dedupe_by_name(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for it in items:
        nm = _place_name(it)
        if not nm:
            continue
        key = nm.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _first_named(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for it in items:
        if _has_real_name(it):
            return it
    return None


# -----------------------------
# Query builder + fallbacks
# -----------------------------
def build_place_queries(payload: TripRequest | dict[str, Any]) -> dict[str, str]:
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
        # make the neighborhood query more explicit
        "neighborhoods": f"best neighborhoods in {destination} (Loop River North West Loop Lincoln Park Wicker Park Old Town Chinatown)".strip(),
    }


def build_restaurants_fallback(destination: str) -> list[dict[str, Any]]:
    return [{"name": f"Top restaurant in {destination}", "address": None, "rating": None}]


def build_hotels_fallback(destination: str) -> list[dict[str, Any]]:
    return [{"name": f"Top hotel in {destination}", "address": None, "rating": None}]


def build_highlights_fallback(destination: str) -> list[dict[str, Any]]:
    return [{"name": f"Top attraction in {destination}", "address": None, "rating": None}]


def build_neighborhoods_fallback() -> list[str]:
    return ["Downtown", "River North", "West Loop", "Lincoln Park"]


# -----------------------------
# Text helpers
# -----------------------------
def _place_text(place: dict[str, Any] | None) -> str:
    if not place:
        return ""
    parts = [
        str(_place_name(place) or ""),
        str(_place_address(place) or ""),
        " ".join(_place_types(place)),
    ]
    return " ".join(p for p in parts if p).lower()


def _place_line(place: dict[str, Any] | None) -> str:
    # If this ever returns "a local spot", dinner/lunch/breakfast was None.
    if not place:
        return "a local spot"
    nm = _place_name(place) or "a local spot"
    addr = _place_address(place)
    return f"{nm} — {addr}" if addr else nm


# -----------------------------
# Neighborhood filtering (prevents CULTURE etc.)
# -----------------------------
_INVALID_NEIGHBORHOOD_WORDS = {
    "culture",
    "food",
    "restaurant",
    "restaurants",
    "attraction",
    "attractions",
    "establishment",
    "point of interest",
}

_NEIGHBORHOOD_HINTS = (
    "loop",
    "park",
    "district",
    "side",
    "square",
    "heights",
    "village",
    "town",
    "river",
    "mile",
    "beach",
    "chinatown",
    "downtown",
    "uptown",
    "old town",
    "west",
    "east",
    "north",
    "south",
)

def _is_neighborhood_like(name: str) -> bool:
    n = (name or "").strip()
    if not n:
        return False
    nl = n.lower()
    if nl in _INVALID_NEIGHBORHOOD_WORDS:
        return False
    return any(h in nl for h in _NEIGHBORHOOD_HINTS)


# -----------------------------
# Scoring
# -----------------------------
DIET_KEYWORDS: dict[str, list[str]] = {
    "vegan": ["vegan", "plant-based", "plant based"],
    "vegetarian": ["vegetarian", "veggie"],
    "gluten-free": ["gluten-free", "gluten free", "gf"],
    "dairy-free": ["dairy-free", "dairy free", "lactose-free", "lactose free"],
    "halal": ["halal"],
    "kosher": ["kosher"],
}

VEGAN_AVOID_KEYWORDS = [
    "steak", "steakhouse", "bbq", "barbecue", "smokehouse",
    "butcher", "meat", "ribs", "burger", "wings",
    "seafood", "fish", "oyster", "lobster", "crab", "shrimp",
    "chicken", "bacon", "sausage",
]


def restaurant_score(place: dict[str, Any], dietary_prefs: list[str]) -> float:
    rating = _place_rating(place) or 0.0
    reviews = float(_place_user_rating_count(place) or 0)
    score = rating * 2.0 + min(math.log1p(reviews), 10.0)

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
    rating = _place_rating(place) or 0.0
    reviews = float(_place_user_rating_count(place) or 0)
    return rating * 2.0 + min(math.log1p(reviews), 10.0)


def rank_restaurants(restaurants: list[dict[str, Any]], dietary_prefs: list[str]) -> list[dict[str, Any]]:
    return sorted(restaurants, key=lambda p: restaurant_score(p, dietary_prefs), reverse=True)


def rank_attractions(highlights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(highlights, key=attraction_score, reverse=True)


# -----------------------------
# Geo helpers + clustering
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
# Meal picking (hard guarantee: dinner never None)
# -----------------------------
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
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """
    Returns (breakfast, lunch, dinner) and guarantees each is non-null and named.
    """
    # Ensure we have at least 1 named candidate
    seed = _first_named(restaurants_ranked)
    if seed is None:
        # last-resort synthetic (should not happen because we fallback earlier)
        seed = {"name": "Dinner recommendation", "address": None}

    scored: list[tuple[float, float, dict[str, Any]]] = []

    for r in restaurants_ranked:
        nm = _place_name(r)
        if not nm:
            continue
        lat = _place_lat(r)
        lng = _place_lng(r)
        dist = 0.0
        if center and lat is not None and lng is not None:
            dist = haversine_m(center[0], center[1], lat, lng)
        scored.append((restaurant_score(r, dietary_prefs), -dist, r))

    scored.sort(reverse=True)

    def pick(prefer_breakfast: bool = False, avoid: set[str] | None = None) -> dict[str, Any] | None:
        avoid = avoid or set()
        # pass 1: avoid used across trip
        for _, __, r in scored:
            nm = _place_name(r)
            if not nm or nm in avoid or nm in used_restaurants:
                continue
            if prefer_breakfast and _meal_kind(r) != "breakfast":
                continue
            used_restaurants.add(nm)
            return r
        # pass 2: allow reuse if needed (avoid duplicates within the day)
        for _, __, r in scored:
            nm = _place_name(r)
            if not nm or nm in avoid:
                continue
            if prefer_breakfast and _meal_kind(r) != "breakfast":
                continue
            return r
        return None

    breakfast = pick(prefer_breakfast=True) or pick(prefer_breakfast=False) or seed
    lunch = pick(prefer_breakfast=False, avoid={_place_name(breakfast) or ""}) or seed
    dinner = pick(prefer_breakfast=False, avoid={_place_name(breakfast) or "", _place_name(lunch) or ""}) or lunch or breakfast or seed

    # Final guarantee
    if not _has_real_name(dinner):
        dinner = lunch
    if not _has_real_name(dinner):
        dinner = breakfast
    if not _has_real_name(dinner):
        dinner = seed

    return breakfast, lunch, dinner


def _blurb(place: dict[str, Any] | None, kind: str) -> str:
    if not place:
        return "A solid pick based on reviews and location."
    name = _place_name(place) or "This spot"
    rating = _place_rating(place)
    cnt = _place_user_rating_count(place)
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
    nm = _place_name(place)
    if lat is None or lng is None or not nm:
        return
    out.append(
        {
            "day": day,
            "category": category,
            "name": nm,
            "address": _place_address(place),
            "lat": lat,
            "lng": lng,
            "google_maps_url": _place_maps_url(place),
            "rating": _place_rating(place),
            "user_rating_count": _place_user_rating_count(place),
        }
    )


# -----------------------------
# Itinerary building
# -----------------------------
def _trip_days(start_date: str, end_date: str) -> int:
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    return max(1, (e - s).days + 1)


def _rotate_neighborhoods(neighborhoods: list[str], days: int) -> list[str]:
    if not neighborhoods:
        return build_neighborhoods_fallback()[:days]
    uniq: list[str] = []
    seen: set[str] = set()
    for n in neighborhoods:
        key = n.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(n.strip())
    if not uniq:
        return build_neighborhoods_fallback()[:days]
    return [uniq[i % len(uniq)] for i in range(days)]


def _pick_diverse_attractions_for_day(
    day_candidates: list[dict[str, Any]],
    used_sites: set[str],
    count: int = ATTRACTIONS_PER_DAY,
) -> list[dict[str, Any] | None]:
    picked: list[dict[str, Any]] = []
    for it in day_candidates:
        nm = _place_name(it)
        if not nm or nm in used_sites:
            continue
        picked.append(it)
        used_sites.add(nm)
        if len(picked) >= count:
            break

    # fill if needed
    for it in day_candidates:
        if len(picked) >= count:
            break
        if it not in picked:
            picked.append(it)

    while len(picked) < count:
        picked.append(None)

    return picked[:count]


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

        # absolute belt+suspenders guarantee
        if not _has_real_name(dinner):
            dinner = lunch
        if not _has_real_name(dinner):
            dinner = breakfast
        if not _has_real_name(dinner):
            dinner = _first_named(restaurants_ranked) or dinner

        _push_place(places, day=day_num, category="breakfast", place=breakfast)
        _push_place(places, day=day_num, category="lunch", place=lunch)
        _push_place(places, day=day_num, category="dinner", place=dinner)
        for s in chosen_sites:
            _push_place(places, day=day_num, category="attraction", place=s)

        hood = neighborhood_plan[i] if i < len(neighborhood_plan) else "Downtown"
        featured_site = next((s for s in chosen_sites if s and _has_real_name(s)), None)

        stops: list[dict[str, Any]] = [{"time_block": "Breakfast", "place": _place_line(breakfast)}]
        for tb, site in zip(["Morning", "Late Morning", "Afternoon", "Late Afternoon"], chosen_sites):
            stops.append({"time_block": tb, "place": _place_line(site)})
        stops.extend(
            [
                {"time_block": "Lunch", "place": _place_line(lunch)},
                {"time_block": "Dinner", "place": _place_line(dinner)},
            ]
        )

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
                        "blurb": f"Today is centered around **{hood}**—keep your stops close to cut transit time.",
                    },
                    "restaurant": {
                        "name": _place_name(dinner) or _place_name(lunch) or _place_name(breakfast),
                        "google_maps_url": _place_maps_url(dinner) or _place_maps_url(lunch) or _place_maps_url(breakfast),
                        "blurb": _blurb(dinner, "dinner"),
                    },
                    "site": {
                        "name": _place_name(featured_site),
                        "google_maps_url": _place_maps_url(featured_site),
                        "blurb": _blurb(featured_site, "site"),
                    },
                },
                "notes": [],
            }
        )

    # de-dupe pins by (day, category, name)
    seen = set()
    deduped: list[dict[str, Any]] = []
    for p in places:
        key = (p.get("day"), p.get("category"), (p.get("name") or "").lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    return itinerary, deduped


@router.post("/generate", response_model=TripGenerateResponse)
def generate_trip(payload: TripRequest) -> TripGenerateResponse:
    try:
        payload = _ensure_trip_request(payload)
        queries = build_place_queries(payload)
        dietary_prefs = _dietary_prefs_from_payload(payload)

        restaurants_raw = safe_search_places(queries["restaurants"], limit=DEFAULT_RESTAURANT_LIMIT)
        hotels_raw = safe_search_places(queries["hotels"], limit=DEFAULT_HOTEL_LIMIT)
        highlights_raw = safe_search_places(queries["highlights"], limit=DEFAULT_HIGHLIGHT_LIMIT)
        neighborhood_raw = safe_search_places(queries["neighborhoods"], limit=DEFAULT_NEIGHBORHOOD_LIMIT)

        weather = safe_get_weather(payload.destination)

        restaurants = [_normalize_place(p) for p in restaurants_raw] if restaurants_raw else build_restaurants_fallback(payload.destination)
        hotels = [_normalize_place(p) for p in hotels_raw] if hotels_raw else build_hotels_fallback(payload.destination)
        highlights = [_normalize_place(p) for p in highlights_raw] if highlights_raw else build_highlights_fallback(payload.destination)

        # filter + dedupe so pickers always have real names
        restaurants = _dedupe_by_name([p for p in restaurants if _has_real_name(p)])
        highlights = _dedupe_by_name([p for p in highlights if _has_real_name(p)])
        hotels = _dedupe_by_name([p for p in hotels if _has_real_name(p)])

        if not restaurants:
            restaurants = build_restaurants_fallback(payload.destination)
        if not highlights:
            highlights = build_highlights_fallback(payload.destination)

        neighborhoods: list[str] = []
        for p in neighborhood_raw:
            np = _normalize_place(p)
            nm = _place_name(np)
            if nm and _is_neighborhood_like(nm):
                neighborhoods.append(nm)
        # unique
        neighborhoods = _rotate_neighborhoods(neighborhoods, days=_trip_days(payload.start_date, payload.end_date))

        itinerary, places = build_rich_days_and_places(
            destination=payload.destination,
            start_date=payload.start_date,
            end_date=payload.end_date,
            restaurants=restaurants,
            highlights=highlights,
            neighborhoods=neighborhoods,
            dietary_prefs=dietary_prefs,
        )

        # legacy pins (optional)
        map_points: list[dict[str, Any]] = []
        for category, items in [("restaurant", restaurants), ("hotel", hotels), ("highlight", highlights)]:
            for item in items:
                lat = _place_lat(item)
                lng = _place_lng(item)
                nm = _place_name(item)
                if lat is None or lng is None or not nm:
                    continue
                map_points.append({"name": nm, "lat": lat, "lng": lng, "category": category})

        summary = payload.notes or f"Trip to {payload.destination}"
        tips = [
            "Keep each day in one area to reduce transit time.",
            "Make dinner reservations for top-rated spots.",
            "Swap indoor/outdoor stops based on weather.",
            "Save Google Maps links for quick navigation.",
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