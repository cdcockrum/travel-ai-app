"use client";

import React, { useEffect, useMemo, useState } from "react";
import MapView from "./map-view";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);

type StoredPersonality = {
  profile_id?: string;
  personality_label?: string;
  summary?: string;
  scores?: Record<string, number>;
  [k: string]: any;
};

type StoredQuizAnswers = {
  dietary_preferences?: string[];
  top_interests?: string[];
  [k: string]: any;
};

type TripRequest = {
  destination: string;
  start_date: string;
  end_date: string;
  notes?: string | null;
  must_see?: string[];
  traveler_profile?: Record<string, any>;
  preferences?: Record<string, any>;
};

type DayMealObj = { place?: string; blurb?: string };
type DayStopObj = { time_block?: string; place?: string };

type ItineraryDay = {
  day?: number;
  title?: string | null;
  meals?: {
    breakfast?: DayMealObj;
    lunch?: DayMealObj;
    dinner?: DayMealObj;
  };
  stops?: DayStopObj[];
  spotlight?: {
    neighborhood?: { name?: string; blurb?: string };
    restaurant?: { name?: string; blurb?: string; google_maps_url?: string | null };
    site?: { name?: string; blurb?: string; google_maps_url?: string | null };
  };
  notes?: string[];
  // fallback old keys
  morning?: string | null;
  afternoon?: string | null;
  evening?: string | null;
  meals_old?: string[];
};

type PlaceLike = {
  name?: string;
  address?: string | null;
  rating?: number | null;
  google_maps_url?: string | null;
  url?: string | null;
  lat?: number | null;
  lng?: number | null;
  [k: string]: any;
};

type TripGenerateResponse = {
  destination?: string;
  summary?: string;
  weather?: any;
  neighborhoods?: string[];
  tips?: any;
  restaurants?: PlaceLike[];
  hotels?: PlaceLike[];
  highlights?: PlaceLike[];
  itinerary?: any[];
  places?: Array<{
    day?: number;
    category: string;
    name: string;
    address?: string | null;
    lat?: number | null;
    lng?: number | null;
    google_maps_url?: string | null;
    rating?: number | null;
    user_rating_count?: number | null;
  }>;
  map_points?: Array<{ name: string; category: string; lat: number; lng: number }>;
};

type MapPlace = {
  name: string;
  address?: string;
  lat?: number | null;
  lng?: number | null;
  category: string;
  google_maps_url?: string | null;
  day?: number;
};

function safeJsonParse<T>(value: string | null): T | null {
  if (!value) return null;
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

async function fetchJsonWithTimeout<T>(
  url: string,
  init: RequestInit,
  timeoutMs: number
): Promise<T> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, { ...init, signal: controller.signal });
    const text = await res.text();
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
    return JSON.parse(text) as T;
  } finally {
    clearTimeout(id);
  }
}

function isPlaceholderPlace(text?: string) {
  const t = (text || "").trim().toLowerCase();
  return !t || t === "—" || t === "a local spot";
}

function SubtleLink({
  href,
  children,
  title,
}: {
  href: string;
  children: React.ReactNode;
  title?: string;
}) {
  // subtle: not blue; only underline on hover
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      title={title}
      className="text-slate-900 decoration-slate-300 underline-offset-4 hover:underline"
    >
      {children}
    </a>
  );
}

function googleMapsSearchUrl(query: string): string {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

function buildMergedNotes(opts: {
  personality: StoredPersonality | null;
  dietaryPrefs: string[];
  notes: string;
  mustDoItems: string;
  avoidItems: string;
}): string {
  const { personality, dietaryPrefs, notes, mustDoItems, avoidItems } = opts;

  const lines: string[] = [];
  if (personality?.personality_label) {
    lines.push(`Traveler personality: ${personality.personality_label}`);
    if (personality.summary) lines.push(personality.summary);
  }
  if (dietaryPrefs.length) lines.push(`Dietary preferences: ${dietaryPrefs.join(", ")}`);
  if (mustDoItems.trim()) lines.push(`Must-do: ${mustDoItems}`);
  if (avoidItems.trim()) lines.push(`Avoid: ${avoidItems}`);
  if (notes.trim()) lines.push(`Notes: ${notes}`);
  return lines.join("\n");
}

function normalizeDay(day: any, index: number): ItineraryDay {
  const dayNum = typeof day?.day === "number" ? day.day : index + 1;
  const title = day?.title ?? null;

  if (day?.meals && !Array.isArray(day.meals)) {
    return {
      day: dayNum,
      title,
      meals: day.meals,
      stops: Array.isArray(day.stops) ? day.stops : [],
      spotlight: day.spotlight || {},
      notes: Array.isArray(day.notes) ? day.notes : [],
    };
  }

  const mealsOld = Array.isArray(day?.meals) ? day.meals : [];
  const stopsFallback: DayStopObj[] = [
    day?.morning ? { time_block: "Morning", place: String(day.morning) } : null,
    day?.afternoon ? { time_block: "Afternoon", place: String(day.afternoon) } : null,
    day?.evening ? { time_block: "Evening", place: String(day.evening) } : null,
  ].filter(Boolean) as DayStopObj[];

  return {
    day: dayNum,
    title,
    stops: stopsFallback,
    notes: Array.isArray(day?.notes) ? day.notes : [],
    morning: day?.morning ?? null,
    afternoon: day?.afternoon ?? null,
    evening: day?.evening ?? null,
    meals_old: mealsOld,
  };
}

function buildGoogleMapsDayRouteUrl(orderedPlaces: MapPlace[]): string {
  const valid = orderedPlaces
    .filter((p) => p.name && typeof p.lat === "number" && typeof p.lng === "number")
    .slice(0, 10);

  if (!valid.length) return "https://www.google.com/maps";

  const coords = valid.map((p) => `${p.lat},${p.lng}`);
  const origin = coords[0];
  const destination = coords[coords.length - 1];
  const waypoints = coords.slice(1, -1);

  const params = new URLSearchParams();
  params.set("api", "1");
  params.set("origin", origin);
  params.set("destination", destination);
  if (waypoints.length) params.set("waypoints", waypoints.join("|"));

  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

function extractNameFromStopText(stopText: string): string {
  // backend often sends: "Name — Address"
  const t = (stopText || "").trim();
  if (!t) return "";
  const parts = t.split("—");
  if (parts.length >= 2) return parts[0].trim();
  // fallback if hyphen used
  const parts2 = t.split(" - ");
  if (parts2.length >= 2) return parts2[0].trim();
  return t;
}

function bestMatchPlaceByName(nameGuess: string, candidates: MapPlace[]): MapPlace | null {
  const g = (nameGuess || "").trim().toLowerCase();
  if (!g) return null;

  let best: { place: MapPlace; score: number } | null = null;

  for (const p of candidates) {
    const n = (p.name || "").trim().toLowerCase();
    if (!n) continue;

    // match if either contains the other
    if (!(n.includes(g) || g.includes(n))) continue;

    // score: prefer closer-length matches (more exact)
    const score = 1000 - Math.abs(n.length - g.length);
    if (!best || score > best.score) best = { place: p, score };
  }

  return best?.place || null;
}

function orderedRoutePlacesForDay(dayNum: number, day: ItineraryDay, allPlaces: MapPlace[]): MapPlace[] {
  const dayPlaces = allPlaces.filter((p) => p.day === dayNum);
  const used = new Set<string>();

  const pushUnique = (p: MapPlace | null) => {
    if (!p) return;
    const key = `${p.category}:${p.name}`.toLowerCase();
    if (used.has(key)) return;
    used.add(key);
    if (typeof p.lat === "number" && typeof p.lng === "number") out.push(p);
  };

  const out: MapPlace[] = [];

  // 1) Use itinerary stops order (best)
  const stops = Array.isArray(day.stops) ? day.stops : [];
  for (const s of stops) {
    const placeText = s.place || "";
    if (isPlaceholderPlace(placeText)) continue;

    const guess = extractNameFromStopText(placeText);
    const match = bestMatchPlaceByName(guess, dayPlaces);
    if (match) {
      pushUnique(match);
      continue;
    }

    // fallback: just search by full text (if we have a place with same-ish name)
    const match2 = bestMatchPlaceByName(placeText, dayPlaces);
    pushUnique(match2);
  }

  // 2) Fallback if stops didn’t resolve well: category order
  if (out.length < 2) {
    const byCat = (cat: string) =>
      dayPlaces.find((p) => (p.category || "").toLowerCase() === cat && typeof p.lat === "number" && typeof p.lng === "number") ||
      null;

    pushUnique(byCat("breakfast"));
    // add a few attractions
    dayPlaces
      .filter((p) => (p.category || "").toLowerCase() === "attraction")
      .slice(0, 4)
      .forEach((p) => pushUnique(p));
    pushUnique(byCat("lunch"));
    pushUnique(byCat("dinner"));
  }

  return out;
}

function guessUrlForText(text: string, dayPlaces: MapPlace[]): string {
  const t = (text || "").toLowerCase();
  const match = dayPlaces.find((p) => p.name && t.includes(p.name.toLowerCase()));
  return match?.google_maps_url || googleMapsSearchUrl(text);
}

function escapeHtml(s: string): string {
  return (s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function buildPrintableHtml(args: {
  trip: TripGenerateResponse;
  itinerary: ItineraryDay[];
  tips: string[];
}): string {
  const { trip, itinerary, tips } = args;

  const title = `${trip.destination || "Trip"} Itinerary`;
  const summary = trip.summary || "";
  const neighborhoods = (trip.neighborhoods || []).join(", ");

  const daysHtml = itinerary
    .map((d) => {
      const meals = d.meals;
      const spotlight = d.spotlight;
      const stops = d.stops || [];

      const mealsHtml = meals
        ? `
          <div class="grid">
            <div><b>Breakfast:</b> ${escapeHtml(meals.breakfast?.place || "—")}<br/><span class="muted">${escapeHtml(meals.breakfast?.blurb || "")}</span></div>
            <div><b>Lunch:</b> ${escapeHtml(meals.lunch?.place || "—")}<br/><span class="muted">${escapeHtml(meals.lunch?.blurb || "")}</span></div>
            <div><b>Dinner:</b> ${escapeHtml(meals.dinner?.place || "—")}<br/><span class="muted">${escapeHtml(meals.dinner?.blurb || "")}</span></div>
          </div>
        `
        : "";

      const spotlightHtml = spotlight
        ? `
          <div class="card">
            <div><b>Neighborhood:</b> ${escapeHtml(spotlight.neighborhood?.name || "—")}</div>
            <div class="muted">${escapeHtml(spotlight.neighborhood?.blurb || "")}</div>
            <div style="height:8px"></div>
            <div><b>Featured restaurant:</b> ${escapeHtml(spotlight.restaurant?.name || "—")}</div>
            <div class="muted">${escapeHtml(spotlight.restaurant?.blurb || "")}</div>
            <div style="height:8px"></div>
            <div><b>Featured site:</b> ${escapeHtml(spotlight.site?.name || "—")}</div>
            <div class="muted">${escapeHtml(spotlight.site?.blurb || "")}</div>
          </div>
        `
        : "";

      const stopsHtml = stops.length
        ? `
          <ul>
            ${stops
              .map(
                (s) =>
                  `<li><b>${escapeHtml(s.time_block || "Stop")}:</b> ${escapeHtml(
                    s.place || "—"
                  )}</li>`
              )
              .join("")}
          </ul>
        `
        : "";

      return `
        <div class="day">
          <h3>Day ${escapeHtml(String(d.day ?? ""))}${d.title ? ` — ${escapeHtml(d.title)}` : ""}</h3>
          ${spotlightHtml}
          ${mealsHtml}
          ${stopsHtml}
        </div>
      `;
    })
    .join("");

  const tipsHtml = tips.length
    ? `<ul>${tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>`
    : "<div class='muted'>No tips.</div>";

  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(title)}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; color:#0f172a; margin: 24px; }
    h1 { margin: 0 0 8px 0; }
    h2 { margin: 24px 0 8px 0; }
    h3 { margin: 18px 0 8px 0; }
    .muted { color: #475569; font-size: 12px; }
    .card { border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; background: #f8fafc; }
    .day { border: 1px solid #e2e8f0; border-radius: 16px; padding: 16px; margin: 12px 0; }
    .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 12px; }
    @media print { body { margin: 0.5in; } }
  </style>
</head>
<body>
  <h1>${escapeHtml(title)}</h1>
  <div class="muted">${escapeHtml(neighborhoods ? `Neighborhoods: ${neighborhoods}` : "")}</div>
  <div style="height:10px"></div>

  <div class="card">
    <b>Summary</b>
    <div style="margin-top:6px">${escapeHtml(summary)}</div>
  </div>

  <h2>Tips</h2>
  ${tipsHtml}

  <h2>Daily Plan</h2>
  ${daysHtml}

  <script>
    setTimeout(() => window.print(), 250);
  </script>
</body>
</html>`;
}

export default function TripBuilderForm() {
  const [destinationCity, setDestinationCity] = useState("Chicago");
  const [destinationCountry, setDestinationCountry] = useState("IL");
  const [startDate, setStartDate] = useState("2026-04-10");
  const [endDate, setEndDate] = useState("2026-04-13");

  const [budgetLevel, setBudgetLevel] = useState("moderate");
  const [mustDoItems, setMustDoItems] = useState("deep dish, architecture tour, museum");
  const [avoidItems, setAvoidItems] = useState("overpacked schedule");
  const [notes, setNotes] = useState("Food, museums, architecture; walkable days.");
  const [dietaryPrefs, setDietaryPrefs] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [trip, setTrip] = useState<TripGenerateResponse | null>(null);

  const [selectedDay, setSelectedDay] = useState<number>(0);
  const [categoryFilter, setCategoryFilter] = useState<Record<string, boolean>>({
    breakfast: true,
    lunch: true,
    dinner: true,
    attraction: true,
  });

  const destination = useMemo(() => {
    const city = destinationCity.trim();
    const country = destinationCountry.trim();
    if (!city) return country;
    if (!country) return city;
    return `${city}, ${country}`;
  }, [destinationCity, destinationCountry]);

  useEffect(() => {
    const savedTrip = safeJsonParse<TripGenerateResponse>(localStorage.getItem("last_trip"));
    if (savedTrip) setTrip(savedTrip);
  }, []);

  const normalizedItinerary = useMemo(() => {
    const raw = trip?.itinerary || [];
    if (!Array.isArray(raw)) return [];
    return raw.map((d, i) => normalizeDay(d, i));
  }, [trip]);

  const availableDays = useMemo(
    () => normalizedItinerary.map((d) => d.day || 0).filter(Boolean),
    [normalizedItinerary]
  );

  const tipsList: string[] = useMemo(() => {
    const t: any = trip?.tips;
    if (Array.isArray(t)) return t.filter((x) => typeof x === "string") as string[];
    if (typeof t === "string" && t.trim()) return [t.trim()];
    return [];
  }, [trip]);

  const defaultTips = useMemo(
    () => [
      "Keep each day in one area to reduce transit time.",
      "Make dinner reservations for top-rated spots.",
      "Swap indoor/outdoor stops based on weather.",
      "Save Google Maps links for quick navigation.",
    ],
    []
  );

  const allPlaces: MapPlace[] = useMemo(() => {
    const ps = trip?.places || [];
    const cleaned = ps
      .map((p) => ({
        name: p.name,
        address: p.address || undefined,
        lat: p.lat ?? null,
        lng: p.lng ?? null,
        category: p.category,
        google_maps_url: p.google_maps_url || null,
        day: p.day,
      }))
      .filter((p) => typeof p.lat === "number" && typeof p.lng === "number");

    if (cleaned.length) return cleaned;

    const mp = trip?.map_points || [];
    return mp.map((p) => ({
      name: p.name,
      category: p.category,
      lat: p.lat,
      lng: p.lng,
    }));
  }, [trip]);

  const mapPlaces: (MapPlace & { order?: number })[] = useMemo(() => {
  let ps = allPlaces;

  // Day filter
  if (selectedDay !== 0) {
    ps = ps.filter((p) => p.day === selectedDay);
  }

  // Category filter
  ps = ps.filter((p) => categoryFilter[(p.category || "").toLowerCase()] !== false);

  // ✅ Number markers only when a specific day is selected
  if (selectedDay === 0) return ps;

  const dayObj = normalizedItinerary.find((d) => d.day === selectedDay);
  const ordered = dayObj ? orderedRoutePlacesForDay(selectedDay, dayObj, allPlaces) : [];

  const keyOf = (p: MapPlace) =>
    `${p.lat},${p.lng},${(p.category || "").toLowerCase()}`;

  const orderMap = new Map<string, number>();
  ordered.forEach((p, idx) => {
    orderMap.set(keyOf(p), idx + 1);
  });

  const withOrder = ps.map((p) => ({
    ...p,
    order: orderMap.get(keyOf(p)),
  }));

  // Sort so numbered pins show first in arrays (optional but nice)
  withOrder.sort((a, b) => (a.order ?? 1e9) - (b.order ?? 1e9));

  return withOrder;
}, [allPlaces, selectedDay, categoryFilter, normalizedItinerary]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setTrip(null);

    try {
      const storedPersonality = safeJsonParse<StoredPersonality>(localStorage.getItem("personality"));
      const storedQuiz = safeJsonParse<StoredQuizAnswers>(localStorage.getItem("quiz_answers"));

      const mergedDietary = Array.from(
        new Set<string>([...(storedQuiz?.dietary_preferences || []), ...(dietaryPrefs || [])])
      );

      const mergedNotes = buildMergedNotes({
        personality: storedPersonality,
        dietaryPrefs: mergedDietary,
        notes,
        mustDoItems,
        avoidItems,
      });

      const payload: TripRequest = {
        destination,
        start_date: startDate,
        end_date: endDate,
        notes: mergedNotes,
        must_see: mustDoItems.split(",").map((s) => s.trim()).filter(Boolean),
        traveler_profile: storedPersonality || {},
        preferences: {
          ...(storedQuiz || {}),
          dietary_preferences: mergedDietary,
          budget_level: budgetLevel,
        },
      };

      const data = await fetchJsonWithTimeout<TripGenerateResponse>(
        `${API_BASE}/api/trips/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
        45_000
      );

      setTrip(data);
      localStorage.setItem("last_trip", JSON.stringify(data));
      setSelectedDay(0);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err?.message || "Something went wrong generating the trip.");
    } finally {
      setLoading(false);
    }
  }

  function handleDownloadPdf() {
    if (!trip) return;
    const html = buildPrintableHtml({
      trip,
      itinerary: normalizedItinerary,
      tips: tipsList.length ? tipsList : defaultTips,
    });
    const w = window.open("", "_blank", "noopener,noreferrer,width=900,height=900");
    if (!w) return;
    w.document.open();
    w.document.write(html);
    w.document.close();
    w.focus();
  }

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8 p-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold text-slate-900">Travel AI</h1>
          <p className="text-slate-600">Routes now follow your itinerary order.</p>
        </div>

        <button
          type="button"
          onClick={handleDownloadPdf}
          disabled={!trip}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 disabled:opacity-50"
          title="Opens print dialog. Choose “Save as PDF”."
        >
          Download PDF
        </button>
      </header>

      <form onSubmit={handleSubmit} className="grid gap-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Destination city</label>
            <input value={destinationCity} onChange={(e) => setDestinationCity(e.target.value)} className="w-full rounded-xl border border-slate-300 px-4 py-3" />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Destination region/country</label>
            <input value={destinationCountry} onChange={(e) => setDestinationCountry(e.target.value)} className="w-full rounded-xl border border-slate-300 px-4 py-3" />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Start date</label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full rounded-xl border border-slate-300 px-4 py-3" />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">End date</label>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full rounded-xl border border-slate-300 px-4 py-3" />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Notes</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} className="w-full rounded-xl border border-slate-300 px-4 py-3" />
          </div>
        </div>

        <div className="flex items-center justify-between gap-3">
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium !text-white hover:bg-slate-800 disabled:opacity-60"
            style={{ color: "#fff" }}
          >
            {loading ? "Generating..." : "Generate Trip"}
          </button>

          {errorMsg ? <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{errorMsg}</div> : null}
        </div>
      </form>

      {trip ? (
        <section className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-900">Map</h3>

              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap gap-2 text-sm">
                  {["breakfast", "lunch", "dinner", "attraction"].map((cat) => (
                    <label key={cat} className="flex cursor-pointer items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1">
                      <input type="checkbox" checked={categoryFilter[cat] ?? true} onChange={(e) => setCategoryFilter((p) => ({ ...p, [cat]: e.target.checked }))} />
                      <span className="capitalize text-slate-700">{cat}</span>
                    </label>
                  ))}
                </div>

                <div className="flex items-center gap-2 text-sm">
                  <span className="text-slate-600">Day:</span>
                  <select className="rounded-lg border border-slate-200 bg-white p-2" value={selectedDay} onChange={(e) => setSelectedDay(Number(e.target.value))}>
                    <option value={0}>All days</option>
                    {availableDays.map((d) => (
                      <option key={d} value={d}>
                        Day {d}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <MapView places={mapPlaces as any} />
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-900">Daily Plan</h3>

              {normalizedItinerary.map((d, idx) => {
                const dayNum = d.day || idx + 1;
                const meals = d.meals;
                const spotlight = d.spotlight;
                const stops = d.stops || [];

                const dayPlaces = allPlaces.filter((p) => p.day === dayNum);
                const orderedForRoute = orderedRoutePlacesForDay(dayNum, d, allPlaces);
                const routeUrl = buildGoogleMapsDayRouteUrl(orderedForRoute);

                return (
                  <div key={dayNum} className="rounded-2xl border border-slate-200 p-5">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="font-semibold text-slate-900">Day {dayNum}</div>
                      <div className="text-sm text-slate-600">{d.title || ""}</div>

                      <SubtleLink href={routeUrl} title="Ordered route: Breakfast → Stops → Lunch → Stops → Dinner">
                        <span className="ml-auto rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
                          Open Day Route
                        </span>
                      </SubtleLink>
                    </div>

                    {spotlight ? (
                      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                        <div className="text-sm font-semibold text-slate-900">Spotlight</div>
                        <div className="mt-2 grid gap-3 md:grid-cols-3">
                          <div>
                            <div className="text-xs font-medium text-slate-600">Neighborhood</div>
                            <div className="mt-1 font-medium text-slate-900">{spotlight.neighborhood?.name || "—"}</div>
                            <div className="mt-1 text-sm text-slate-700">{spotlight.neighborhood?.blurb || ""}</div>
                          </div>

                          <div>
                            <div className="text-xs font-medium text-slate-600">Featured restaurant</div>
                            <div className="mt-1 font-medium text-slate-900">
                              {spotlight.restaurant?.name ? (
                                <SubtleLink href={spotlight.restaurant.google_maps_url || googleMapsSearchUrl(spotlight.restaurant.name)} title="Open in Google Maps">
                                  {spotlight.restaurant.name}
                                </SubtleLink>
                              ) : (
                                "—"
                              )}
                            </div>
                            <div className="mt-1 text-sm text-slate-700">{spotlight.restaurant?.blurb || ""}</div>
                          </div>

                          <div>
                            <div className="text-xs font-medium text-slate-600">Featured site</div>
                            <div className="mt-1 font-medium text-slate-900">
                              {spotlight.site?.name ? (
                                <SubtleLink href={spotlight.site.google_maps_url || googleMapsSearchUrl(spotlight.site.name)} title="Open in Google Maps">
                                  {spotlight.site.name}
                                </SubtleLink>
                              ) : (
                                "—"
                              )}
                            </div>
                            <div className="mt-1 text-sm text-slate-700">{spotlight.site?.blurb || ""}</div>
                          </div>
                        </div>
                      </div>
                    ) : null}

                    {meals ? (
                      <div className="mt-4 grid gap-3 md:grid-cols-3">
                        {(["breakfast", "lunch", "dinner"] as const).map((k) => {
                          const placeText = meals[k]?.place || "—";
                          const href = !isPlaceholderPlace(placeText) ? guessUrlForText(placeText, dayPlaces) : "";
                          return (
                            <div key={k} className="rounded-xl border border-slate-200 p-4">
                              <div className="text-xs font-medium text-slate-600">{k[0].toUpperCase() + k.slice(1)}</div>
                              <div className="mt-1 font-medium text-slate-900">
                                {!isPlaceholderPlace(placeText) ? (
                                  <SubtleLink href={href} title="Open in Google Maps">
                                    {placeText}
                                  </SubtleLink>
                                ) : (
                                  <span>{placeText}</span>
                                )}
                              </div>
                              <div className="mt-1 text-sm text-slate-700">{meals[k]?.blurb || ""}</div>
                            </div>
                          );
                        })}
                      </div>
                    ) : null}

                    {stops.length ? (
                      <div className="mt-4">
                        <div className="text-sm font-semibold text-slate-900">Stops</div>
                        <ul className="mt-2 space-y-2">
                          {stops.map((s, i) => {
                            const placeText = s.place || "—";
                            const href = !isPlaceholderPlace(placeText) ? guessUrlForText(placeText, dayPlaces) : "";
                            return (
                              <li key={i} className="rounded-xl border border-slate-100 p-3">
                                <div className="text-xs font-medium text-slate-600">{s.time_block || "Stop"}</div>
                                <div className="mt-1 font-medium text-slate-900">
                                  {!isPlaceholderPlace(placeText) ? (
                                    <SubtleLink href={href} title="Open in Google Maps">
                                      {placeText}
                                    </SubtleLink>
                                  ) : (
                                    <span>{placeText}</span>
                                  )}
                                </div>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>

          <aside className="space-y-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900">Tips</h3>
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
                {(tipsList.length ? tipsList : defaultTips).map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900">Top Restaurants</h3>
              <ul className="mt-3 space-y-2 text-sm text-slate-700">
                {(trip.restaurants || []).slice(0, 8).map((r, i) => {
                  const name = r.name || "—";
                  const href = 
                    r.google_maps_url || r.url || (r.name ? googleMapsSearchUrl(r.name) : "");
                  return (
                    <li key={i} className="rounded-lg border border-slate-100 p-3">
                      <div className="font-medium text-slate-900">
                        {r.name && href ? <SubtleLink href={href}>{name}</SubtleLink> : name}
                      </div>
                      {r.address ? <div className="text-slate-600">{r.address}</div> : null}
                      {r.rating != null ? <div className="mt-1 text-slate-600">⭐ {r.rating}</div> : null}
                    </li>
                  );
                })}
              </ul>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900">Top Highlights</h3>
              <ul className="mt-3 space-y-2 text-sm text-slate-700">
                {(trip.highlights || []).slice(0, 8).map((h, i) => {
                  const name = h.name || "—";
                  const href =
                    h.google_maps_url || h.url || (h.name ? googleMapsSearchUrl(h.name) : "");
                  return (
                    <li key={i} className="rounded-lg border border-slate-100 p-3">
                      <div className="font-medium text-slate-900">
                        {h.name && href ? <SubtleLink href={href}>{name}</SubtleLink> : name}
                      </div>
                      {h.address ? <div className="text-slate-600">{h.address}</div> : null}
                      {h.rating != null ? <div className="mt-1 text-slate-600">⭐ {h.rating}</div> : null}
                    </li>
                  );
                })}
              </ul>
            </div>
          </aside>
        </section>
      ) : null}
    </div>
  );
}