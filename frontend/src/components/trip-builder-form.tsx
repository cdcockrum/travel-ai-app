"use client";

import { useEffect, useMemo, useState } from "react";
import TripResultsMap from "@/components/trip-results-map";

type Personality = {
  profile_id?: string;
  personality_label?: string;
  summary?: string;
  scores?: Record<string, number>;
};

type QuizAnswers = {
  pace_level?: string;
  budget_level?: string;
  travel_party?: string;
  walking_tolerance?: string;
  top_interests?: string[];
  food_adventure_level?: string;
  lodging_preference?: string;
  convenience_vs_authenticity?: number;
  structure_preference?: string;
  transit_confidence?: string;
  deal_breakers?: string[];
  meal_style?: string;
  trip_values?: string[];
  dietary_preferences?: string[];
  allergies?: string[];
  accessibility_needs?: string[];
  crowd_tolerance?: string;
  day_start_preference?: string;
  nightlife_interest?: string;
  shopping_interest?: string;
  wellness_interest?: string;
  photography_interest?: string;
  weather_tolerance?: string;
  social_energy?: string;
  seat_of_pants_factor?: string;
  neighborhood_style?: string[];
  preferred_meal_times?: string[];
  transport_preferences?: string[];
};

type DayPlan = {
  day: number;
  title?: string;
  morning?: string;
  afternoon?: string;
  evening?: string;
  meals?: string[];
  notes?: string[];
};

type PlaceCard = {
  name: string;
  address?: string;
  rating?: number;
  types?: string[];
  price_level?: number;
  summary?: string;
  lat?: number;
  lng?: number;
};

type WeatherSummary = {
  description?: string;
  temperature_c?: number;
  feels_like_c?: number;
  humidity?: number;
};

type MapPoint = {
  name: string;
  category: string;
  lat: number;
  lng: number;
};

type TripResponse = {
  destination?: string;
  summary?: string;
  weather?: WeatherSummary | null;
  neighborhoods?: string[];
  restaurants?: PlaceCard[];
  hotels?: PlaceCard[];
  highlights?: PlaceCard[];
  map_points?: MapPoint[];
  tips?: string[];
  itinerary?: DayPlan[];
};

function priceLabel(priceLevel?: number) {
  if (priceLevel === undefined || priceLevel === null) return null;
  return "$".repeat(Math.max(1, Math.min(priceLevel, 4)));
}

function PlaceSection({
  title,
  items,
}: {
  title: string;
  items?: PlaceCard[];
}) {
  if (!items?.length) return null;

  return (
    <div>
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {items.map((item, index) => (
          <div
            key={`${title}-${item.name}-${index}`}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <p className="font-semibold text-slate-900">{item.name}</p>

            {item.address ? (
              <p className="mt-1 text-sm text-slate-600">{item.address}</p>
            ) : null}

            <div className="mt-2 space-y-1 text-sm text-slate-700">
              {item.rating ? <p>Rating: {item.rating}</p> : null}
              {priceLabel(item.price_level) ? (
                <p>Price: {priceLabel(item.price_level)}</p>
              ) : null}
              {item.types?.length ? (
                <p>Types: {item.types.slice(0, 3).join(", ")}</p>
              ) : null}
              {item.summary ? <p>{item.summary}</p> : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TripBuilderForm() {
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [travelNotes, setTravelNotes] = useState("");
  const [mustSee, setMustSee] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TripResponse | null>(null);

  const [quizAnswers, setQuizAnswers] = useState<QuizAnswers>({});
  const [personality, setPersonality] = useState<Personality>({});

  useEffect(() => {
    const savedQuiz = localStorage.getItem("quiz_answers");
    const savedPersonality = localStorage.getItem("personality");

    if (savedQuiz) {
      try {
        setQuizAnswers(JSON.parse(savedQuiz));
      } catch (error) {
        console.error("Could not parse quiz_answers", error);
      }
    }

    if (savedPersonality) {
      try {
        setPersonality(JSON.parse(savedPersonality));
      } catch (error) {
        console.error("Could not parse personality", error);
      }
    }
  }, []);

  const travelerSnapshot = useMemo(() => {
    const parts = [
      personality.personality_label,
      quizAnswers.budget_level,
      quizAnswers.pace_level,
      quizAnswers.day_start_preference,
    ].filter(Boolean);

    return parts.join(" • ");
  }, [personality, quizAnswers]);

  const tripLengthText = useMemo(() => {
    if (!startDate || !endDate) return "";
    const start = new Date(startDate);
    const end = new Date(endDate);
    const ms = end.getTime() - start.getTime();
    if (Number.isNaN(ms) || ms < 0) return "";
    const days = Math.floor(ms / (1000 * 60 * 60 * 24)) + 1;
    return `${days} day${days === 1 ? "" : "s"}`;
  }, [startDate, endDate]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (!destination || !startDate || !endDate) {
      alert("Please fill out destination, start date, and end date.");
      return;
    }

    const payload = {
      destination,
      start_date: startDate,
      end_date: endDate,
      notes: travelNotes,
      must_see: mustSee
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      traveler_profile: personality,
      preferences: {
        pace: quizAnswers.pace_level ?? null,
        budget: quizAnswers.budget_level ?? null,
        travel_party: quizAnswers.travel_party ?? null,
        walking_tolerance: quizAnswers.walking_tolerance ?? null,
        food_adventure_level: quizAnswers.food_adventure_level ?? null,
        lodging_preference: quizAnswers.lodging_preference ?? null,
        convenience_vs_authenticity:
          quizAnswers.convenience_vs_authenticity ?? null,
        structure_preference: quizAnswers.structure_preference ?? null,
        transit_confidence: quizAnswers.transit_confidence ?? null,
        deal_breakers: quizAnswers.deal_breakers ?? [],
        meal_style: quizAnswers.meal_style ?? null,
        trip_values: quizAnswers.trip_values ?? [],
        dietary_preferences: quizAnswers.dietary_preferences ?? [],
        allergies: quizAnswers.allergies ?? [],
        accessibility_needs: quizAnswers.accessibility_needs ?? [],
        crowd_tolerance: quizAnswers.crowd_tolerance ?? null,
        day_start_preference: quizAnswers.day_start_preference ?? null,
        nightlife_interest: quizAnswers.nightlife_interest ?? null,
        shopping_interest: quizAnswers.shopping_interest ?? null,
        wellness_interest: quizAnswers.wellness_interest ?? null,
        photography_interest: quizAnswers.photography_interest ?? null,
        weather_tolerance: quizAnswers.weather_tolerance ?? null,
        social_energy: quizAnswers.social_energy ?? null,
        seat_of_pants_factor: quizAnswers.seat_of_pants_factor ?? null,
        neighborhood_style: quizAnswers.neighborhood_style ?? [],
        preferred_meal_times: quizAnswers.preferred_meal_times ?? [],
        transport_preferences: quizAnswers.transport_preferences ?? [],
        top_interests: quizAnswers.top_interests ?? [],
      },
    };

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/trips/generate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to generate trip");
      }

      const data = await response.json();
      console.log("TRIP API RESPONSE:", data);
      console.log("MAP POINTS:", data.map_points);
      setResult(data);
    } catch (error) {
      console.error(error);
      alert("Something went wrong generating the trip.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
          Build Your Trip
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Create a richer itinerary using your saved travel personality, food
          preferences, comfort needs, and destination priorities.
        </p>

        {travelerSnapshot ? (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Loaded traveler profile
            </p>
            <p className="mt-1 text-sm font-medium text-slate-900">
              {travelerSnapshot}
            </p>
            {personality.summary ? (
              <p className="mt-2 text-sm text-slate-600">{personality.summary}</p>
            ) : null}
          </div>
        ) : null}
      </div>

      <form onSubmit={handleSubmit} className="grid gap-8">
        <section className="grid gap-6">
          <h2 className="text-lg font-semibold text-slate-900">Trip details</h2>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Destination
              </label>
              <input
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="Tokyo"
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              />
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">
                  Start date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">
                  End date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                />
              </div>
            </div>
          </div>

          {startDate && endDate && tripLengthText ? (
            <p className="text-sm text-slate-500">
              Trip length: {tripLengthText}
            </p>
          ) : null}

          <div className="grid gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Must-see places or priorities
              </label>
              <input
                value={mustSee}
                onChange={(e) => setMustSee(e.target.value)}
                placeholder="TeamLab, vintage shopping, quiet cafés"
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              />
              <p className="text-xs text-slate-500">
                Separate multiple items with commas.
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Extra notes
              </label>
              <textarea
                value={travelNotes}
                onChange={(e) => setTravelNotes(e.target.value)}
                rows={5}
                placeholder="We want slower mornings, memorable food, easy transit, strong architecture, and low-crowd evenings."
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              />
            </div>
          </div>
        </section>

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={loading}
            className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium !text-white transition hover:bg-slate-700 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate Trip"}
          </button>

          <button
            type="button"
            onClick={() => {
              localStorage.removeItem("quiz_answers");
              localStorage.removeItem("personality");
              setQuizAnswers({});
              setPersonality({});
            }}
            className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-medium !text-slate-900 transition hover:bg-slate-50"
          >
            Clear saved quiz
          </button>
        </div>
      </form>

      {result ? (
        <div className="space-y-6 rounded-3xl border border-slate-200 bg-slate-50 p-6">
          <div>
            <h2 className="text-2xl font-semibold text-slate-950">
              {result.destination || destination}
            </h2>
            {result.summary ? (
              <p className="mt-2 text-slate-700">{result.summary}</p>
            ) : null}
          </div>

          {result.weather ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900">Weather</h3>
              <p className="mt-2 text-slate-700">
                {result.weather.description || "Current conditions unavailable"}
                {result.weather.temperature_c !== undefined &&
                result.weather.temperature_c !== null
                  ? ` • ${result.weather.temperature_c}°C`
                  : ""}
              </p>
              {(result.weather.feels_like_c !== undefined &&
                result.weather.feels_like_c !== null) ||
              (result.weather.humidity !== undefined &&
                result.weather.humidity !== null) ? (
                <p className="text-sm text-slate-600">
                  {result.weather.feels_like_c !== undefined &&
                  result.weather.feels_like_c !== null
                    ? `Feels like ${result.weather.feels_like_c}°C`
                    : ""}
                  {result.weather.feels_like_c !== undefined &&
                  result.weather.feels_like_c !== null &&
                  result.weather.humidity !== undefined &&
                  result.weather.humidity !== null
                    ? " • "
                    : ""}
                  {result.weather.humidity !== undefined &&
                  result.weather.humidity !== null
                    ? `Humidity ${result.weather.humidity}%`
                    : ""}
                </p>
              ) : null}
            </div>
          ) : null}

          {result.neighborhoods?.length ? (
            <div>
              <h3 className="text-lg font-semibold text-slate-900">
                Suggested neighborhoods
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {result.neighborhoods.map((item) => (
                  <span
                    key={item}
                    className="rounded-full border border-slate-300 bg-white px-3 py-1 text-sm text-slate-900"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {result.map_points?.length ? (
            <TripResultsMap points={result.map_points} />
          ) : null}

          <PlaceSection title="Highlights" items={result.highlights} />
          <PlaceSection title="Restaurant ideas" items={result.restaurants} />
          <PlaceSection title="Hotel ideas" items={result.hotels} />

          {result.itinerary?.length ? (
            <div>
              <h3 className="text-lg font-semibold text-slate-900">
                Day-by-day itinerary
              </h3>
              <div className="mt-4 space-y-4">
                {result.itinerary.map((day) => (
                  <div
                    key={day.day}
                    className="rounded-2xl border border-slate-200 bg-white p-4"
                  >
                    <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                      Day {day.day}
                    </p>

                    {day.title ? (
                      <h4 className="mt-1 text-lg font-semibold text-slate-950">
                        {day.title}
                      </h4>
                    ) : null}

                    <div className="mt-3 space-y-2 text-sm text-slate-700">
                      {day.morning ? (
                        <p>
                          <span className="font-medium text-slate-900">Morning:</span>{" "}
                          {day.morning}
                        </p>
                      ) : null}
                      {day.afternoon ? (
                        <p>
                          <span className="font-medium text-slate-900">Afternoon:</span>{" "}
                          {day.afternoon}
                        </p>
                      ) : null}
                      {day.evening ? (
                        <p>
                          <span className="font-medium text-slate-900">Evening:</span>{" "}
                          {day.evening}
                        </p>
                      ) : null}
                    </div>

                    {day.meals?.length ? (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-slate-900">Meals</p>
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                          {day.meals.map((meal, index) => (
                            <li key={`${meal}-${index}`}>{meal}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}

                    {day.notes?.length ? (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-slate-900">Notes</p>
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                          {day.notes.map((note, index) => (
                            <li key={`${note}-${index}`}>{note}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {result.tips?.length ? (
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Tips</h3>
              <ul className="mt-3 list-disc space-y-1 pl-5 text-slate-700">
                {result.tips.map((tip, index) => (
                  <li key={`${tip}-${index}`}>{tip}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
