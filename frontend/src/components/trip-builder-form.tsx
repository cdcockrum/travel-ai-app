"use client";

import { useEffect, useMemo, useState } from "react";
import MapView from "./map-view";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type ItineraryPlace = {
  name: string;
  address?: string;
  lat?: number | null;
  lng?: number | null;
  category: string;
  google_maps_url?: string | null;
  why?: string;
  best_for?: string;
};

type ItineraryDay = {
  day_number: number;
  theme: string;
  neighborhood: string;
  narrative?: string;
  morning: string[];
  breakfast?: string[];
  lunch?: string[];
  afternoon: string[];
  dinner?: string[];
  evening: string[];
  places?: ItineraryPlace[];
  practical_note: string;
};

type ItineraryResponse = {
  trip_id?: string;
  trip_summary: string;
  score?: number;
  strengths?: string[];
  weaknesses?: string[];
  improvements?: string[];
  days: ItineraryDay[];
};

type StoredPersonality = {
  profile_id: string;
  personality_label: string;
  summary: string;
  scores: Record<string, number>;
};

type StoredQuizAnswers = {
  pace_level: string;
  budget_level: string;
  travel_party: string;
  walking_tolerance: string;
  top_interests: string[];
  food_adventure_level: string;
  lodging_preference: string;
  convenience_vs_authenticity: number;
  structure_preference: string;
  transit_confidence: string;
  deal_breakers: string[];
  meal_style: string;
  trip_values: string[];
  dietary_preferences?: string[];
  allergies?: string[];
  accessibility_needs?: string[];
  crowd_tolerance?: string;
  day_start_preference?: string;
};

type PlaceRecommendation = {
  id: string;
  name: string;
  address?: string;
  rating?: number;
  user_rating_count?: number;
  primary_type?: string;
  google_maps_url?: string;
  website_url?: string;
  types?: string[];
};

type HotelRecommendation = {
  id: string;
  name: string;
  area: string;
  style: string;
  price_band: string;
  why: string;
};

type RecommendationsResponse = {
  trip_id: string;
  destination_city: string;
  destination_country: string;
  restaurants: PlaceRecommendation[];
  attractions: PlaceRecommendation[];
  hotels: HotelRecommendation[];
  errors?: string[];
};

type WeatherDay = {
  date: string;
  avg_temp: number;
  condition: string;
};

type WeatherResponse = {
  city: string;
  country: string;
  forecast: WeatherDay[];
};

type IntelligenceResponse = {
  city: string;
  best_times: string;
  crowds: string;
  tip: string;
};

function SectionList({
  title,
  items,
}: {
  title: string;
  items?: string[];
}) {
  if (!items || items.length === 0) return null;

  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {title}
      </p>
      <ul className="mt-2 space-y-1.5 text-sm leading-6 text-slate-800">
        {items.map((item) => (
          <li key={item}>• {item}</li>
        ))}
      </ul>
    </div>
  );
}

function TagList({
  title,
  items,
  tone = "slate",
}: {
  title: string;
  items?: string[];
  tone?: "slate" | "emerald" | "indigo" | "rose" | "amber";
}) {
  if (!items || items.length === 0) return null;

  const tones = {
    slate: "border-slate-200 bg-slate-50 text-slate-700",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-800",
    indigo: "border-indigo-200 bg-indigo-50 text-indigo-800",
    rose: "border-rose-200 bg-rose-50 text-rose-800",
    amber: "border-amber-200 bg-amber-50 text-amber-800",
  };

  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {title}
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className={`rounded-full border px-3 py-1 text-xs font-medium ${tones[tone]}`}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function recommendationReason(
  place: PlaceRecommendation,
  dietaryPrefs: string[] = []
) {
  const types = (place.types || []).join(" ").toLowerCase();
  const name = (place.name || "").toLowerCase();

  if (
    dietaryPrefs.includes("vegan") &&
    (types.includes("vegan") || name.includes("vegan"))
  ) {
    return "Best for vegan-friendly dining";
  }

  if (
    dietaryPrefs.includes("vegetarian") &&
    (types.includes("vegetarian") ||
      name.includes("vegetarian") ||
      name.includes("veggie"))
  ) {
    return "Best for vegetarian-friendly dining";
  }

  if ((place.rating || 0) >= 4.6) {
    return "Best for standout reviews";
  }

  if (types.includes("cafe")) {
    return "Best for a lighter stop";
  }

  if (types.includes("museum")) {
    return "Best for cultural depth";
  }

  if (types.includes("tourist_attraction")) {
    return "Best for iconic sightseeing";
  }

  return "Best for neighborhood fit";
}

export default function TripBuilderForm() {
  const [destinationCity, setDestinationCity] = useState("Tokyo");
  const [destinationCountry, setDestinationCountry] = useState("Japan");
  const [startDate, setStartDate] = useState("2026-04-10");
  const [endDate, setEndDate] = useState("2026-04-15");
  const [budgetLevel, setBudgetLevel] = useState("moderate");
  const [mustDoItems, setMustDoItems] = useState("food tour, temple visit");
  const [avoidItems, setAvoidItems] = useState("overpacked days");
  const [notes, setNotes] = useState(
    "First trip focused on food, culture, and walkable neighborhoods"
  );
  const [dietaryPrefs, setDietaryPrefs] = useState<string[]>([
    "vegan",
    "vegetarian",
  ]);

  const [loading, setLoading] = useState(false);
  const [itinerary, setItinerary] = useState<ItineraryResponse | null>(null);
  const [recommendations, setRecommendations] =
    useState<RecommendationsResponse | null>(null);
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [intel, setIntel] = useState<IntelligenceResponse | null>(null);
  const [personality, setPersonality] = useState<StoredPersonality | null>(null);
  const [quizAnswers, setQuizAnswers] = useState<StoredQuizAnswers | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("last_trip");
    if (saved) {
      try {
        setItinerary(JSON.parse(saved));
      } catch (error) {
        console.error("Failed to parse saved trip", error);
      }
    }
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setItinerary(null);
    setRecommendations(null);
    setWeather(null);
    setIntel(null);

    try {
      const storedPersonality = localStorage.getItem("personality");
      const storedQuizAnswers = localStorage.getItem("quiz_answers");

      const parsedPersonality: StoredPersonality | null = storedPersonality
        ? JSON.parse(storedPersonality)
        : null;

      const parsedQuizAnswers: StoredQuizAnswers | null = storedQuizAnswers
        ? JSON.parse(storedQuizAnswers)
        : null;

      const mergedQuizAnswers = parsedQuizAnswers
        ? {
            ...parsedQuizAnswers,
            dietary_preferences: Array.from(
              new Set([
                ...(parsedQuizAnswers.dietary_preferences || []),
                ...dietaryPrefs,
              ])
            ),
          }
        : {
            dietary_preferences: dietaryPrefs,
          };

      setPersonality(parsedPersonality);
      setQuizAnswers(mergedQuizAnswers as StoredQuizAnswers);

      const mergedNotes = parsedPersonality
        ? `Traveler personality: ${parsedPersonality.personality_label}. ${parsedPersonality.summary} Dietary preferences: ${dietaryPrefs.join(", ")}. Notes: ${notes}`
        : `Dietary preferences: ${dietaryPrefs.join(", ")}. Notes: ${notes}`;

      const tripResponse = await fetch(`${API_BASE}/api/trips`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: `${destinationCity} Trip`,
          destination_city: destinationCity,
          destination_country: destinationCountry,
          start_date: startDate,
          end_date: endDate,
          budget_level: budgetLevel,
          must_do_items: mustDoItems
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          avoid_items: avoidItems
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          notes: mergedNotes,
          profile: mergedQuizAnswers,
        }),
      });

      if (!tripResponse.ok) {
        throw new Error("Failed to create trip");
      }

      const tripData = await tripResponse.json();

      const itineraryResponse = await fetch(`${API_BASE}/api/itinerary/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          trip_id: tripData.trip_id,
        }),
      });

      if (!itineraryResponse.ok) {
        throw new Error("Failed to generate itinerary");
      }

      const itineraryData: ItineraryResponse = await itineraryResponse.json();
      setItinerary(itineraryData);
      localStorage.setItem("last_trip", JSON.stringify(itineraryData));

      const recResponse = await fetch(
        `${API_BASE}/api/recommendations/${tripData.trip_id}`
      );

      if (recResponse.ok) {
        const recData: RecommendationsResponse = await recResponse.json();
        setRecommendations(recData);
      }

      const weatherResponse = await fetch(
        `${API_BASE}/api/weather/${encodeURIComponent(
          destinationCity
        )}/${encodeURIComponent(destinationCountry)}`
      );

      if (weatherResponse.ok) {
        const weatherData: WeatherResponse = await weatherResponse.json();
        setWeather(weatherData);
      }

      const intelResponse = await fetch(
        `${API_BASE}/intelligence/${encodeURIComponent(destinationCity)}`
      );

      if (intelResponse.ok) {
        const intelData: IntelligenceResponse = await intelResponse.json();
        setIntel(intelData);
      }
    } catch (error) {
      console.error(error);
      alert("Something went wrong generating the itinerary.");
    } finally {
      setLoading(false);
    }
  }

  const allPlaces = itinerary?.days.flatMap((day) => day.places || []) || [];

  const featuredNeighborhood = useMemo(() => {
    if (!itinerary?.days?.length) return null;

    const counts = new Map<string, number>();
    itinerary.days.forEach((day) => {
      counts.set(day.neighborhood, (counts.get(day.neighborhood) || 0) + 1);
    });

    return [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || null;
  }, [itinerary]);

  const featuredRestaurant = useMemo(() => {
    return recommendations?.restaurants?.[0] || null;
  }, [recommendations]);

  const travelTips = useMemo(() => {
    const tips: string[] = [];

    if (quizAnswers?.dietary_preferences?.includes("vegan")) {
      tips.push(
        "Keep a shortlist of vegan-friendly restaurants pinned before each day starts."
      );
    }
    if (quizAnswers?.dietary_preferences?.includes("vegetarian")) {
      tips.push(
        "Small cafés and neighborhood restaurants may offer better vegetarian flexibility than larger chains."
      );
    }
    if (quizAnswers?.allergies?.length) {
      tips.push(
        "Keep allergy needs written clearly so they are easy to show quickly when ordering."
      );
    }
    if (quizAnswers?.walking_tolerance === "low") {
      tips.push(
        "Favor one strong neighborhood per day instead of crossing the city repeatedly."
      );
    }
    if (quizAnswers?.crowd_tolerance === "low") {
      tips.push(
        "Aim for early or late windows when visiting high-profile attractions."
      );
    }
    if (quizAnswers?.day_start_preference === "late") {
      tips.push(
        "Avoid locking in too many early reservations so mornings stay comfortable."
      );
    }
    if (quizAnswers?.transit_confidence === "not comfortable") {
      tips.push(
        "Save map links in advance and prioritize simpler routes over faster but more complex ones."
      );
    }
    if (
      quizAnswers?.convenience_vs_authenticity &&
      quizAnswers.convenience_vs_authenticity >= 4
    ) {
      tips.push(
        "Allow extra time for neighborhood discoveries, since more local areas often move at a slower pace."
      );
    }
    if (tips.length === 0) {
      tips.push(
        "Anchor each day to one neighborhood so the trip feels lighter and easier to navigate."
      );
      tips.push(
        "Use one strong meal or reservation per day, then leave some room around it."
      );
    }

    return tips.slice(0, 4);
  }, [quizAnswers]);

  const alerts = useMemo(() => {
    const items: string[] = [];

    if (quizAnswers?.allergies?.length) {
      items.push(
        "Meal safety alert: verify ingredients and prep details before ordering."
      );
    }
    if (quizAnswers?.walking_tolerance === "low") {
      items.push(
        "Mobility alert: avoid stacking multiple long sightseeing blocks back-to-back."
      );
    }
    if (quizAnswers?.crowd_tolerance === "low") {
      items.push(
        "Crowd alert: major sights may feel best outside midday peaks."
      );
    }
    if (quizAnswers?.structure_preference === "fully planned") {
      items.push(
        "Planning alert: this trip benefits from a few fixed anchors each day."
      );
    }

    return items.slice(0, 3);
  }, [quizAnswers]);

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight text-slate-950">
          AI Travel Intelligence Platform
        </h1>
        <p className="max-w-3xl text-slate-600">
          Build smarter, more personal itineraries with neighborhood-aware
          planning, stronger recommendations, and a more natural day-by-day
          rhythm.
        </p>
      </div>

      <div className="grid gap-8 xl:grid-cols-[1fr,1.2fr,0.8fr]">
        <form
          onSubmit={handleSubmit}
          className="glass-card space-y-5 rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-sm"
        >
          <div>
            <h2 className="text-2xl font-semibold text-slate-950">
              Build a Trip
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Enter real trip details and generate a personalized itinerary.
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-800">
              Destination city
            </label>
            <input
              value={destinationCity}
              onChange={(e) => setDestinationCity(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none placeholder:text-slate-400 focus:border-slate-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-800">
              Destination country
            </label>
            <input
              value={destinationCountry}
              onChange={(e) => setDestinationCountry(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none placeholder:text-slate-400 focus:border-slate-500"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-800">
                Start date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-slate-500"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-800">
                End date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-slate-500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-800">
              Budget level
            </label>
            <select
              value={budgetLevel}
              onChange={(e) => setBudgetLevel(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
            >
              <option value="budget">Budget</option>
              <option value="moderate">Moderate</option>
              <option value="premium">Premium</option>
              <option value="luxury">Luxury</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-800">
              Dietary preferences
            </label>
            <div className="grid grid-cols-2 gap-2 text-sm text-slate-800">
              {[
                "vegan",
                "vegetarian",
                "gluten-free",
                "dairy-free",
                "halal",
                "kosher",
              ].map((option) => {
                const checked = dietaryPrefs.includes(option);
                return (
                  <label
                    key={option}
                    className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setDietaryPrefs((prev) => [...prev, option]);
                        } else {
                          setDietaryPrefs((prev) =>
                            prev.filter((item) => item !== option)
                          );
                        }
                      }}
                    />
                    <span className="capitalize">{option}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-800">
              Must-do items
            </label>
            <input
              value={mustDoItems}
              onChange={(e) => setMustDoItems(e.target.value)}
              placeholder="food tour, architecture walk, museum"
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none placeholder:text-slate-400 focus:border-slate-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-800">
              Avoid items
            </label>
            <input
              value={avoidItems}
              onChange={(e) => setAvoidItems(e.target.value)}
              placeholder="long transit, nightlife-heavy plans"
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none placeholder:text-slate-400 focus:border-slate-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-800">Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none placeholder:text-slate-400 focus:border-slate-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-black px-5 py-3 text-base font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="text-white">
              {loading ? "Generating..." : "Generate Trip"}
            </span>
          </button>
        </form>

        <div className="space-y-6">
          {itinerary ? (
            <>
              <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-slate-950">Overview</h2>
                <p className="mt-3 leading-7 text-slate-800">
                  {itinerary.trip_summary}
                </p>
              </div>

              <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-slate-950">
                  Travel Intelligence
                </h2>

                {featuredNeighborhood && (
                  <p className="mt-3 text-sm text-slate-800">
                    Featured neighborhood:{" "}
                    <span className="font-semibold">{featuredNeighborhood}</span>
                  </p>
                )}

                {featuredRestaurant && (
                  <p className="mt-2 text-sm text-slate-800">
                    Featured restaurant:{" "}
                    <span className="font-semibold">{featuredRestaurant.name}</span>
                  </p>
                )}

                {intel && (
                  <div className="mt-4 space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm text-slate-700">
                      <span className="font-semibold">Best times:</span>{" "}
                      {intel.best_times}
                    </p>
                    <p className="text-sm text-slate-700">
                      <span className="font-semibold">Crowd insight:</span>{" "}
                      {intel.crowds}
                    </p>
                    <p className="text-sm text-slate-700">
                      <span className="font-semibold">Tip:</span> {intel.tip}
                    </p>
                  </div>
                )}

                {weather?.forecast?.length ? (
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {weather.forecast.map((day) => (
                      <div
                        key={day.date}
                        className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                      >
                        <p className="text-sm font-semibold text-slate-900">
                          {day.date}
                        </p>
                        <p className="mt-1 text-sm text-slate-700">
                          {day.condition}
                        </p>
                        <p className="mt-1 text-sm text-slate-700">
                          Avg temp: {day.avg_temp}°C
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-600">
                    Weather preview unavailable right now.
                  </p>
                )}

                <div className="mt-5 space-y-4">
                  <TagList title="Travel tips" items={travelTips} tone="indigo" />
                  <TagList title="Alerts" items={alerts} tone="rose" />
                </div>
              </div>

              <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-4 shadow-sm">
                <h2 className="mb-4 text-xl font-semibold text-slate-950">Map</h2>
                <MapView places={allPlaces} />
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                {itinerary.days.map((day) => (
                  <div
                    key={day.day_number}
                    className="glass-card rounded-3xl border border-slate-200 bg-white/80 p-5 shadow-md transition hover:-translate-y-1 hover:shadow-xl"
                  >
                    <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                      Day {day.day_number}
                    </p>
                    <h3 className="mt-2 text-xl font-semibold text-slate-950">
                      {day.theme}
                    </h3>
                    <p className="mt-1 text-sm text-slate-600">{day.neighborhood}</p>

                    {day.narrative && (
                      <p className="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700">
                        {day.narrative}
                      </p>
                    )}

                    <div className="mt-4 space-y-4">
                      <SectionList title="Morning" items={day.morning} />
                      <SectionList title="Breakfast" items={day.breakfast} />
                      <SectionList title="Lunch" items={day.lunch} />
                      <SectionList title="Afternoon" items={day.afternoon} />
                      <SectionList title="Dinner" items={day.dinner} />
                      <SectionList title="Evening" items={day.evening} />
                    </div>

                    {day.places && day.places.length > 0 && (
                      <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                          Selected stops
                        </p>

                        <div className="mt-3 space-y-3">
                          {day.places.map((place) => (
                            <div
                              key={`${day.day_number}-${place.name}-${place.category}`}
                              className="rounded-xl border border-slate-200 bg-white p-3"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <p className="font-medium text-slate-900">
                                    {place.name}
                                  </p>
                                  <p className="mt-1 text-xs text-slate-500">
                                    {place.category}
                                  </p>
                                </div>

                                {place.best_for && (
                                  <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-800">
                                    {place.best_for}
                                  </span>
                                )}
                              </div>

                              {place.why && (
                                <p className="mt-2 text-sm leading-6 text-slate-700">
                                  {place.why}
                                </p>
                              )}

                              {place.google_maps_url && (
                                <a
                                  href={place.google_maps_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mt-2 inline-block text-sm text-blue-700 underline"
                                >
                                  Open in Maps
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <p className="mt-4 text-sm italic leading-6 text-slate-600">
                      {day.practical_note}
                    </p>
                  </div>
                ))}
              </div>

              {recommendations?.errors && recommendations.errors.length > 0 && (
                <div className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                  {recommendations.errors.map((error) => (
                    <p key={error}>{error}</p>
                  ))}
                </div>
              )}

              {recommendations?.hotels && (
                <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-sm">
                  <h2 className="text-xl font-semibold text-slate-950">
                    Suggested Hotels
                  </h2>
                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    {recommendations.hotels.map((hotel) => (
                      <div
                        key={hotel.id}
                        className="rounded-2xl border border-slate-200 bg-white p-4"
                      >
                        <p className="font-semibold text-slate-950">{hotel.name}</p>
                        <p className="mt-1 text-sm text-slate-600">{hotel.area}</p>
                        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                          {hotel.style} • {hotel.price_band}
                        </p>
                        <p className="mt-3 text-sm leading-6 text-slate-800">
                          {hotel.why}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {recommendations && (
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-sm">
                    <h2 className="text-xl font-semibold text-slate-950">
                      Restaurants
                    </h2>
                    {recommendations.restaurants.length === 0 ? (
                      <p className="mt-3 text-sm text-slate-700">
                        No restaurant recommendations found yet.
                      </p>
                    ) : (
                      <div className="mt-4 space-y-4">
                        {recommendations.restaurants.map((place) => (
                          <div
                            key={place.id}
                            className="rounded-2xl border border-slate-200 bg-white p-4"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="font-semibold text-slate-950">
                                  {place.name}
                                </p>
                                <p className="mt-2 text-sm text-slate-600">
                                  {recommendationReason(
                                    place,
                                    quizAnswers?.dietary_preferences ||
                                      dietaryPrefs
                                  )}
                                </p>
                              </div>

                              <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-[11px] font-medium text-indigo-800">
                                {recommendationReason(
                                  place,
                                  quizAnswers?.dietary_preferences ||
                                    dietaryPrefs
                                )}
                              </span>
                            </div>

                            {place.address && (
                              <p className="mt-3 text-sm text-slate-600">
                                {place.address}
                              </p>
                            )}
                            {place.rating && (
                              <p className="mt-3 text-sm text-slate-800">
                                ⭐ {place.rating}
                                {place.user_rating_count
                                  ? ` (${place.user_rating_count} reviews)`
                                  : ""}
                              </p>
                            )}
                            {place.google_maps_url && (
                              <a
                                href={place.google_maps_url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-3 inline-block text-sm text-blue-700 underline"
                              >
                                View on Maps
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-sm">
                    <h2 className="text-xl font-semibold text-slate-950">
                      Attractions
                    </h2>
                    {recommendations.attractions.length === 0 ? (
                      <p className="mt-3 text-sm text-slate-700">
                        No attraction recommendations found yet.
                      </p>
                    ) : (
                      <div className="mt-4 space-y-4">
                        {recommendations.attractions.map((place) => (
                          <div
                            key={place.id}
                            className="rounded-2xl border border-slate-200 bg-white p-4"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="font-semibold text-slate-950">
                                  {place.name}
                                </p>
                                <p className="mt-2 text-sm text-slate-600">
                                  {recommendationReason(place)}
                                </p>
                              </div>

                              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-800">
                                {recommendationReason(place)}
                              </span>
                            </div>

                            {place.address && (
                              <p className="mt-3 text-sm text-slate-600">
                                {place.address}
                              </p>
                            )}
                            {place.rating && (
                              <p className="mt-3 text-sm text-slate-800">
                                ⭐ {place.rating}
                                {place.user_rating_count
                                  ? ` (${place.user_rating_count} reviews)`
                                  : ""}
                              </p>
                            )}
                            {place.google_maps_url && (
                              <a
                                href={place.google_maps_url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-3 inline-block text-sm text-blue-700 underline"
                              >
                                View on Maps
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-950">
                Trip Output
              </h2>
              <p className="mt-2 text-slate-700">
                Your itinerary, map, hotels, recommendations, and travel
                intelligence will appear here.
              </p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-950">
              Profile Driving This Trip
            </h2>

            {personality || quizAnswers ? (
              <div className="mt-4 space-y-5">
                {personality && (
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      {personality.personality_label}
                    </p>
                    <p className="mt-1 text-sm leading-6 text-slate-700">
                      {personality.summary}
                    </p>
                  </div>
                )}

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Pace
                    </p>
                    <p className="mt-1 text-sm text-slate-800">
                      {quizAnswers?.pace_level || "Not set"}
                    </p>
                  </div>

                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Walking
                    </p>
                    <p className="mt-1 text-sm text-slate-800">
                      {quizAnswers?.walking_tolerance || "Not set"}
                    </p>
                  </div>

                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Structure
                    </p>
                    <p className="mt-1 text-sm text-slate-800">
                      {quizAnswers?.structure_preference || "Not set"}
                    </p>
                  </div>

                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Day start
                    </p>
                    <p className="mt-1 text-sm text-slate-800">
                      {quizAnswers?.day_start_preference || "Not set"}
                    </p>
                  </div>

                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Crowd tolerance
                    </p>
                    <p className="mt-1 text-sm text-slate-800">
                      {quizAnswers?.crowd_tolerance || "Not set"}
                    </p>
                  </div>

                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Transit confidence
                    </p>
                    <p className="mt-1 text-sm text-slate-800">
                      {quizAnswers?.transit_confidence || "Not set"}
                    </p>
                  </div>
                </div>

                <TagList
                  title="Top interests"
                  items={quizAnswers?.top_interests}
                  tone="emerald"
                />
                <TagList
                  title="Dietary preferences"
                  items={quizAnswers?.dietary_preferences}
                  tone="indigo"
                />
                <TagList
                  title="Accessibility needs"
                  items={quizAnswers?.accessibility_needs}
                  tone="rose"
                />
                <TagList
                  title="Deal breakers"
                  items={quizAnswers?.deal_breakers}
                  tone="amber"
                />
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-700">
                No saved quiz profile found yet. You can still build a trip
                manually.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}