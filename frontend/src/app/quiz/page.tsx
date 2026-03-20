"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

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

const accessibilityOptions = [
  "wheelchair accessible",
  "low walking",
  "step-free routes",
  "near transit",
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

function ToggleGroup({
  title,
  items,
  selected,
  onToggle,
  activeClassName,
}: {
  title: string;
  items: string[];
  selected: string[];
  onToggle: (item: string) => void;
  activeClassName: string;
}) {
  return (
    <div>
      <p className="text-sm font-medium text-slate-800">{title}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => onToggle(item)}
            className={`rounded-full border px-4 py-2 text-sm transition ${
              selected.includes(item)
                ? `${activeClassName} text-white`
                : "border-slate-300 bg-white text-slate-800"
            }`}
          >
            <span className={selected.includes(item) ? "text-white" : ""}>
              {item}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

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
            Save your travel style so the itinerary builder can personalize your
            trip more intelligently.
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
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
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
                    setAnswers((prev) => ({
                      ...prev,
                      budget_level: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option value="budget">Budget</option>
                  <option value="moderate">Moderate</option>
                  <option value="premium">Premium</option>
                  <option value="luxury">Luxury</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">
                  Travel party
                </label>
                <select
                  value={answers.travel_party}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      travel_party: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option value="solo">Solo</option>
                  <option value="couple">Couple</option>
                  <option value="family">Family</option>
                  <option value="friends">Friends</option>
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
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option value="low">Low</option>
                  <option value="moderate">Moderate</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">
                  Food adventure level
                </label>
                <select
                  value={answers.food_adventure_level}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      food_adventure_level: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option value="low">Low</option>
                  <option value="moderate">Moderate</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">
                  Lodging preference
                </label>
                <select
                  value={answers.lodging_preference}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      lodging_preference: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option value="boutique hotel">Boutique hotel</option>
                  <option value="standard hotel">Standard hotel</option>
                  <option value="luxury hotel">Luxury hotel</option>
                  <option value="apartment">Apartment</option>
                  <option value="hostel">Hostel</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-800">
                  Structure preference
                </label>
                <select
                  value={answers.structure_preference}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      structure_preference: e.target.value,
                    }))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option value="fully planned">Fully planned</option>
                  <option value="some structure with flexibility">
                    Some structure with flexibility
                  </option>
                  <option value="mostly spontaneous">Mostly spontaneous</option>
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
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option value="not comfortable">Not comfortable</option>
                  <option value="comfortable">Comfortable</option>
                  <option value="very comfortable">Very comfortable</option>
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
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
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
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
                >
                  <option value="early">Early</option>
                  <option value="mid-morning">Mid-morning</option>
                  <option value="late">Late</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-800">
                Convenience vs authenticity
              </label>
              <input
                type="range"
                min={1}
                max={5}
                value={answers.convenience_vs_authenticity}
                onChange={(e) =>
                  setAnswers((prev) => ({
                    ...prev,
                    convenience_vs_authenticity: Number(e.target.value),
                  }))
                }
                className="mt-3 w-full"
              />
              <p className="mt-2 text-sm text-slate-600">
                {answers.convenience_vs_authenticity === 1
                  ? "Strongly prefer convenience"
                  : answers.convenience_vs_authenticity === 5
                  ? "Strongly prefer authenticity"
                  : "Balanced between convenience and authenticity"}
              </p>
            </div>

            <ToggleGroup
              title="Top interests"
              items={interestOptions}
              selected={answers.top_interests}
              onToggle={(item) => toggleItem("top_interests", item)}
              activeClassName="border-slate-900 bg-slate-900"
            />

            <ToggleGroup
              title="Dietary preferences"
              items={dietaryOptions}
              selected={answers.dietary_preferences}
              onToggle={(item) => toggleItem("dietary_preferences", item)}
              activeClassName="border-indigo-700 bg-indigo-700"
            />

            <ToggleGroup
              title="Accessibility needs"
              items={accessibilityOptions}
              selected={answers.accessibility_needs}
              onToggle={(item) => toggleItem("accessibility_needs", item)}
              activeClassName="border-emerald-700 bg-emerald-700"
            />

            <ToggleGroup
              title="Deal breakers"
              items={dealBreakerOptions}
              selected={answers.deal_breakers}
              onToggle={(item) => toggleItem("deal_breakers", item)}
              activeClassName="border-rose-700 bg-rose-700"
            />

            <ToggleGroup
              title="Trip values"
              items={tripValueOptions}
              selected={answers.trip_values}
              onToggle={(item) => toggleItem("trip_values", item)}
              activeClassName="border-amber-700 bg-amber-700"
            />

            <div>
              <label className="text-sm font-medium text-slate-800">
                Meal style
              </label>
              <select
                value={answers.meal_style}
                onChange={(e) =>
                  setAnswers((prev) => ({
                    ...prev,
                    meal_style: e.target.value,
                  }))
                }
                className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="mostly spontaneous">Mostly spontaneous</option>
                <option value="mix of planned and spontaneous">
                  Mix of planned and spontaneous
                </option>
                <option value="reservation-heavy">Reservation-heavy</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full rounded-2xl bg-slate-950 px-5 py-3 text-base font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              <span className="text-white">Save quiz and continue</span>
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}