"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type QuizAnswers = {
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
  dietary_preferences: string[];
  allergies: string[];
  accessibility_needs: string[];
  crowd_tolerance: string;
  day_start_preference: string;
};

const interestOptions = [
  "food",
  "local culture",
  "architecture",
  "nature",
  "shopping",
  "museums",
  "nightlife",
  "wellness",
];

const dietaryOptions = [
  "vegan",
  "vegetarian",
  "gluten-free",
  "dairy-free",
  "halal",
  "kosher",
];

const dealBreakerOptions = [
  "long transit times",
  "overpacked days",
  "tourist traps",
  "nightlife-heavy areas",
  "expensive dining only",
];

const tripValueOptions = [
  "comfort",
  "authenticity",
  "efficiency",
  "spontaneity",
  "food quality",
  "cultural depth",
];

export default function QuizPage() {
  const router = useRouter();

  const [answers, setAnswers] = useState<QuizAnswers>({
    pace_level: "balanced",
    budget_level: "moderate",
    travel_party: "solo",
    walking_tolerance: "moderate",
    top_interests: ["food", "local culture"],
    food_adventure_level: "moderate",
    lodging_preference: "boutique hotel",
    convenience_vs_authenticity: 3,
    structure_preference: "some structure with flexibility",
    transit_confidence: "comfortable",
    deal_breakers: ["overpacked days"],
    meal_style: "mix of planned and spontaneous",
    trip_values: ["authenticity", "food quality"],
    dietary_preferences: [],
    allergies: [],
    accessibility_needs: [],
    crowd_tolerance: "moderate",
    day_start_preference: "mid-morning",
  });

  function toggleItem(field: keyof QuizAnswers, value: string) {
    const current = answers[field] as string[];
    const next = current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value];

    setAnswers((prev) => ({
      ...prev,
      [field]: next,
    }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    localStorage.setItem("quiz_answers", JSON.stringify(answers));

    const personality = {
      profile_id: "local-profile",
      personality_label: "Balanced Cultural Explorer",
      summary:
        "Enjoys a thoughtful mix of food, local character, and structured flexibility without overloading the day.",
      scores: {
        balance: 8,
        culture: 8,
        food: 8,
        comfort: 6,
      },
    };

    localStorage.setItem("personality", JSON.stringify(personality));
    router.push("/trip-builder");
  }

  return (
    <main className="min-h-screen px-4 py-10">
      <div className="mx-auto max-w-4xl">
        <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-8 shadow-sm">
          <h1 className="text-3xl font-bold tracking-tight text-slate-950">
            Traveler Quiz
          </h1>
          <p className="mt-2 text-slate-600">
            Save your travel style so the itinerary builder can personalize your trip.
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-8">
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium text-slate-800">Pace</label>
                <select
                  value={answers.pace_level}
                  onChange={(e) =>
                    setAnswers((prev) => ({ ...prev, pace_level: e.target.value }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                >
                  <option value="relaxed">Relaxed</option>
                  <option value="balanced">Balanced</option>
                  <option value="packed">Packed</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">Budget</label>
                <select
                  value={answers.budget_level}
                  onChange={(e) =>
                    setAnswers((prev) => ({ ...prev, budget_level: e.target.value }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                >
                  <option value="budget">Budget</option>
                  <option value="moderate">Moderate</option>
                  <option value="premium">Premium</option>
                  <option value="luxury">Luxury</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">
                  Walking tolerance
                </label>
                <select
                  value={answers.walking_tolerance}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      walking_tolerance: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                >
                  <option value="low">Low</option>
                  <option value="moderate">Moderate</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">
                  Day start preference
                </label>
                <select
                  value={answers.day_start_preference}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      day_start_preference: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                >
                  <option value="early">Early</option>
                  <option value="mid-morning">Mid-morning</option>
                  <option value="late">Late</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">
                  Crowd tolerance
                </label>
                <select
                  value={answers.crowd_tolerance}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      crowd_tolerance: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                >
                  <option value="low">Low</option>
                  <option value="moderate">Moderate</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">
                  Transit confidence
                </label>
                <select
                  value={answers.transit_confidence}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      transit_confidence: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                >
                  <option value="not comfortable">Not comfortable</option>
                  <option value="comfortable">Comfortable</option>
                  <option value="very comfortable">Very comfortable</option>
                </select>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-800">Top interests</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {interestOptions.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleItem("top_interests", item)}
                    className={`rounded-full border px-4 py-2 text-sm ${
                      answers.top_interests.includes(item)
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-slate-300 bg-white text-slate-800"
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-800">Dietary preferences</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {dietaryOptions.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleItem("dietary_preferences", item)}
                    className={`rounded-full border px-4 py-2 text-sm ${
                      answers.dietary_preferences.includes(item)
                        ? "border-indigo-700 bg-indigo-700 text-white"
                        : "border-slate-300 bg-white text-slate-800"
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-800">Deal breakers</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {dealBreakerOptions.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleItem("deal_breakers", item)}
                    className={`rounded-full border px-4 py-2 text-sm ${
                      answers.deal_breakers.includes(item)
                        ? "border-rose-700 bg-rose-700 text-white"
                        : "border-slate-300 bg-white text-slate-800"
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-800">Trip values</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {tripValueOptions.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleItem("trip_values", item)}
                    className={`rounded-full border px-4 py-2 text-sm ${
                      answers.trip_values.includes(item)
                        ? "border-emerald-700 bg-emerald-700 text-white"
                        : "border-slate-300 bg-white text-slate-800"
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              className="w-full rounded-2xl bg-slate-950 px-5 py-3 text-base font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              Save quiz and continue
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
