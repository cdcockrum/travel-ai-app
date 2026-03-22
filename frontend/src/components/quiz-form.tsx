"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

type QuizResult = {
  profile_id: string;
  personality_label: string;
  summary: string;
  scores: Record<string, number>;
};

const INTEREST_OPTIONS = [
  "food",
  "architecture",
  "local culture",
  "museums",
  "nature",
  "shopping",
  "nightlife",
  "photography",
  "wellness",
  "coffee & cafés",
];

const DIETARY_OPTIONS = [
  "vegan",
  "vegetarian",
  "pescatarian",
  "halal",
  "kosher",
  "gluten-free",
  "dairy-free",
  "low-carb",
  "low-sodium",
  "nut-free",
  "shellfish-free",
  "egg-free",
  "soy-free",
  "sesame-free",
  "no pork",
  "no beef",
  "no alcohol",
  "low spice",
];

const ALLERGY_OPTIONS = [
  "nut allergy",
  "peanut allergy",
  "shellfish allergy",
  "dairy allergy",
  "gluten allergy",
  "soy allergy",
  "egg allergy",
  "sesame allergy",
];

const ACCESSIBILITY_OPTIONS = [
  "low walking preferred",
  "wheelchair accessibility",
  "stairs avoidance",
  "easy restroom access",
  "sensory-friendly spaces",
  "frequent rest breaks",
  "step-free routes",
  "minimal standing",
  "near transit",
];

const DEALBREAKER_OPTIONS = [
  "long walking days",
  "early mornings",
  "crowded tourist areas",
  "expensive dining",
  "aggressive schedules",
  "complicated transit",
  "too many reservations",
  "nightlife-heavy areas",
  "long waits",
];

const TRIP_VALUE_OPTIONS = [
  "feeling inspired",
  "relaxing",
  "seeing a lot",
  "eating well",
  "learning something new",
  "experiencing local culture",
  "finding beauty",
  "efficiency",
  "hidden gems",
];

const NEIGHBORHOOD_STYLE_OPTIONS = [
  "quiet and local",
  "walkable and lively",
  "historic",
  "food-centric",
  "design-forward",
  "green and peaceful",
  "luxury-oriented",
];

const MEAL_TIME_OPTIONS = [
  "quick breakfasts",
  "slow café mornings",
  "light lunches",
  "sit-down lunches",
  "street food flexibility",
  "reservation dinners",
  "dessert/snack stops",
];

const TRANSPORT_OPTIONS = [
  "public transit",
  "walking",
  "taxi/rideshare",
  "private transfers",
  "minimal transfers",
  "bike-friendly",
];

function toggleArrayValue(current: string[], value: string, maxSelections?: number) {
  if (current.includes(value)) {
    return current.filter((item) => item !== value);
  }

  if (maxSelections && current.length >= maxSelections) {
    return [...current.slice(1), value];
  }

  return [...current, value];
}

function ToggleGroup({
  title,
  subtitle,
  items,
  selected,
  onToggle,
  activeClassName,
  maxSelections,
}: {
  title: string;
  subtitle?: string;
  items: string[];
  selected: string[];
  onToggle: (item: string) => void;
  activeClassName: string;
  maxSelections?: number;
}) {
  return (
    <div className="space-y-3">
      <div>
        <label className="text-sm font-medium text-slate-700">{title}</label>
        {subtitle ? (
          <p className="mt-1 text-xs text-slate-500">
            {subtitle}
            {maxSelections ? ` (up to ${maxSelections})` : ""}
          </p>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-2">
        {items.map((item) => {
          const isSelected = selected.includes(item);

          return (
            <button
              key={item}
              type="button"
              onClick={() => onToggle(item)}
              className={[
                "rounded-full border px-4 py-2 text-sm font-medium transition",
                isSelected
                  ? `${activeClassName} !text-white`
                  : "border-slate-300 bg-white !text-slate-900 hover:bg-slate-50",
              ].join(" ")}
            >
              {item}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function QuizForm() {
  const router = useRouter();

  const [paceLevel, setPaceLevel] = useState("balanced");
  const [budgetLevel, setBudgetLevel] = useState("moderate");
  const [travelParty, setTravelParty] = useState("partner");
  const [walkingTolerance, setWalkingTolerance] = useState("moderate");
  const [foodAdventureLevel, setFoodAdventureLevel] = useState("high");
  const [lodgingPreference, setLodgingPreference] = useState("boutique");
  const [convenienceVsAuthenticity, setConvenienceVsAuthenticity] = useState(4);
  const [structurePreference, setStructurePreference] = useState(
    "some structure with flexibility"
  );
  const [transitConfidence, setTransitConfidence] = useState("somewhat comfortable");
  const [mealStyle, setMealStyle] = useState("casual local");
  const [crowdTolerance, setCrowdTolerance] = useState("moderate");
  const [dayStartPreference, setDayStartPreference] = useState("mid-morning");

  const [nightlifeInterest, setNightlifeInterest] = useState("moderate");
  const [shoppingInterest, setShoppingInterest] = useState("moderate");
  const [wellnessInterest, setWellnessInterest] = useState("low");
  const [photographyInterest, setPhotographyInterest] = useState("moderate");
  const [weatherTolerance, setWeatherTolerance] = useState("moderate");
  const [socialEnergy, setSocialEnergy] = useState("balanced");
  const [seatOfPantsFactor, setSeatOfPantsFactor] = useState("moderate");

  const [selectedInterests, setSelectedInterests] = useState<string[]>([
    "food",
    "architecture",
    "local culture",
  ]);
  const [dealBreakers, setDealBreakers] = useState<string[]>([
    "aggressive schedules",
    "complicated transit",
  ]);
  const [tripValues, setTripValues] = useState<string[]>([
    "eating well",
    "experiencing local culture",
  ]);
  const [dietaryPreferences, setDietaryPreferences] = useState<string[]>([]);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [accessibilityNeeds, setAccessibilityNeeds] = useState<string[]>([]);
  const [neighborhoodStyle, setNeighborhoodStyle] = useState<string[]>([
    "walkable and lively",
  ]);
  const [preferredMealTimes, setPreferredMealTimes] = useState<string[]>([
    "slow café mornings",
    "reservation dinners",
  ]);
  const [transportPreferences, setTransportPreferences] = useState<string[]>([
    "public transit",
    "walking",
  ]);

  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(false);

  function toggleValue(
    value: string,
    setter: React.Dispatch<React.SetStateAction<string[]>>,
    maxSelections?: number
  ) {
    setter((prev) => toggleArrayValue(prev, value, maxSelections));
  }

  const convenienceLabel = useMemo(() => {
    if (convenienceVsAuthenticity === 1) return "Strongly prefer convenience";
    if (convenienceVsAuthenticity === 2) return "Mostly prefer convenience";
    if (convenienceVsAuthenticity === 3) return "Balanced";
    if (convenienceVsAuthenticity === 4) return "Mostly prefer authenticity";
    return "Strongly prefer authenticity";
  }, [convenienceVsAuthenticity]);

  async function handleSubmit() {
    if (selectedInterests.length === 0) {
      alert("Please choose at least one interest.");
      return;
    }

    if (tripValues.length === 0) {
      alert("Please choose at least one trip value.");
      return;
    }

    const payload = {
      pace_level: paceLevel,
      budget_level: budgetLevel,
      travel_party: travelParty,
      walking_tolerance: walkingTolerance,
      top_interests: selectedInterests,
      food_adventure_level: foodAdventureLevel,
      lodging_preference: lodgingPreference,
      convenience_vs_authenticity: convenienceVsAuthenticity,
      structure_preference: structurePreference,
      transit_confidence: transitConfidence,
      deal_breakers: dealBreakers,
      meal_style: mealStyle,
      trip_values: tripValues,
      dietary_preferences: dietaryPreferences,
      allergies,
      accessibility_needs: accessibilityNeeds,
      crowd_tolerance: crowdTolerance,
      day_start_preference: dayStartPreference,
      nightlife_interest: nightlifeInterest,
      shopping_interest: shoppingInterest,
      wellness_interest: wellnessInterest,
      photography_interest: photographyInterest,
      weather_tolerance: weatherTolerance,
      social_energy: socialEnergy,
      seat_of_pants_factor: seatOfPantsFactor,
      neighborhood_style: neighborhoodStyle,
      preferred_meal_times: preferredMealTimes,
      transport_preferences: transportPreferences,
    };

    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/api/profile/quiz`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to submit quiz");
      }

      const data: QuizResult = await response.json();
      setResult(data);

      localStorage.setItem("personality", JSON.stringify(data));
      localStorage.setItem("quiz_answers", JSON.stringify(payload));

      setTimeout(() => {
        router.push("/trip-builder");
      }, 700);
    } catch (error) {
      console.error(error);
      alert("Something went wrong submitting the quiz.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
          Travel Personality Quiz
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Answer a few questions so the app can personalize destinations, food,
          pacing, logistics, comfort, and neighborhood vibe.
        </p>
      </div>

      <div className="grid gap-8">
        <section className="grid gap-6">
          <h2 className="text-lg font-semibold text-slate-900">Core travel style</h2>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Travel pace</label>
              <select
                value={paceLevel}
                onChange={(e) => setPaceLevel(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="relaxed">Relaxed</option>
                <option value="balanced">Balanced</option>
                <option value="packed">Packed</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Budget level</label>
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
              <label className="text-sm font-medium text-slate-700">Travel party</label>
              <select
                value={travelParty}
                onChange={(e) => setTravelParty(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="solo">Solo</option>
                <option value="partner">Partner</option>
                <option value="friends">Friends</option>
                <option value="family">Family</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Day start preference
              </label>
              <select
                value={dayStartPreference}
                onChange={(e) => setDayStartPreference(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="early">Early start</option>
                <option value="mid-morning">Mid-morning</option>
                <option value="late">Late start</option>
              </select>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Structure preference
              </label>
              <select
                value={structurePreference}
                onChange={(e) => setStructurePreference(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="fully planned">Fully planned</option>
                <option value="some structure with flexibility">
                  Some structure with flexibility
                </option>
                <option value="mostly spontaneous">Mostly spontaneous</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Seat-of-the-pants factor
              </label>
              <select
                value={seatOfPantsFactor}
                onChange={(e) => setSeatOfPantsFactor(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700">
              Convenience vs authenticity ({convenienceVsAuthenticity}/5)
            </label>
            <input
              type="range"
              min="1"
              max="5"
              value={convenienceVsAuthenticity}
              onChange={(e) => setConvenienceVsAuthenticity(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-slate-500">{convenienceLabel}</p>
          </div>
        </section>

        <section className="grid gap-6">
          <h2 className="text-lg font-semibold text-slate-900">Comfort and logistics</h2>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Walking tolerance
              </label>
              <select
                value={walkingTolerance}
                onChange={(e) => setWalkingTolerance(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Crowd tolerance
              </label>
              <select
                value={crowdTolerance}
                onChange={(e) => setCrowdTolerance(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Prefer quieter places</option>
                <option value="moderate">Moderate</option>
                <option value="high">Crowds are okay</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Transit confidence
              </label>
              <select
                value={transitConfidence}
                onChange={(e) => setTransitConfidence(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="not comfortable">Not very comfortable</option>
                <option value="somewhat comfortable">Somewhat comfortable</option>
                <option value="very comfortable">Very comfortable</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Weather tolerance
              </label>
              <select
                value={weatherTolerance}
                onChange={(e) => setWeatherTolerance(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Lodging preference
              </label>
              <select
                value={lodgingPreference}
                onChange={(e) => setLodgingPreference(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="budget hotel">Budget hotel</option>
                <option value="standard hotel">Standard hotel</option>
                <option value="boutique">Boutique hotel</option>
                <option value="luxury">Luxury hotel</option>
                <option value="local stay">Local/unique stay</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Meal style</label>
              <select
                value={mealStyle}
                onChange={(e) => setMealStyle(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="quick and affordable">Quick and affordable</option>
                <option value="casual local">Casual local</option>
                <option value="curated dining">Curated dining</option>
                <option value="fine dining">Fine dining</option>
              </select>
            </div>
          </div>

          <ToggleGroup
            title="Accessibility and comfort needs"
            subtitle="These help the trip builder avoid friction"
            items={ACCESSIBILITY_OPTIONS}
            selected={accessibilityNeeds}
            onToggle={(item) => toggleValue(item, setAccessibilityNeeds)}
            activeClassName="border-indigo-700 bg-indigo-700"
          />

          <ToggleGroup
            title="Preferred transportation modes"
            subtitle="Choose how you most like getting around"
            items={TRANSPORT_OPTIONS}
            selected={transportPreferences}
            onToggle={(item) => toggleValue(item, setTransportPreferences, 3)}
            activeClassName="border-sky-700 bg-sky-700"
            maxSelections={3}
          />
        </section>

        <section className="grid gap-6">
          <h2 className="text-lg font-semibold text-slate-900">Experiences and vibe</h2>

          <ToggleGroup
            title="Top interests"
            subtitle="Choose the experiences that matter most"
            items={INTEREST_OPTIONS}
            selected={selectedInterests}
            onToggle={(item) => toggleValue(item, setSelectedInterests, 5)}
            activeClassName="border-slate-900 bg-slate-900"
            maxSelections={5}
          />

          <ToggleGroup
            title="Neighborhood style"
            subtitle="What kinds of areas feel best to you?"
            items={NEIGHBORHOOD_STYLE_OPTIONS}
            selected={neighborhoodStyle}
            onToggle={(item) => toggleValue(item, setNeighborhoodStyle, 3)}
            activeClassName="border-cyan-700 bg-cyan-700"
            maxSelections={3}
          />

          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Food adventurousness
              </label>
              <select
                value={foodAdventureLevel}
                onChange={(e) => setFoodAdventureLevel(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Prefer familiar food</option>
                <option value="moderate">Somewhat adventurous</option>
                <option value="high">Very adventurous</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Nightlife interest
              </label>
              <select
                value={nightlifeInterest}
                onChange={(e) => setNightlifeInterest(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Shopping interest
              </label>
              <select
                value={shoppingInterest}
                onChange={(e) => setShoppingInterest(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Wellness interest
              </label>
              <select
                value={wellnessInterest}
                onChange={(e) => setWellnessInterest(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Photography interest
              </label>
              <select
                value={photographyInterest}
                onChange={(e) => setPhotographyInterest(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Social energy</label>
              <select
                value={socialEnergy}
                onChange={(e) => setSocialEnergy(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900"
              >
                <option value="quiet">Quiet</option>
                <option value="balanced">Balanced</option>
                <option value="social">Social</option>
              </select>
            </div>
          </div>

          <ToggleGroup
            title="Deal-breakers"
            subtitle="Avoid these where possible"
            items={DEALBREAKER_OPTIONS}
            selected={dealBreakers}
            onToggle={(item) => toggleValue(item, setDealBreakers)}
            activeClassName="border-rose-700 bg-rose-700"
          />

          <ToggleGroup
            title="What matters most on a great trip?"
            subtitle="These shape the overall vibe of your itinerary"
            items={TRIP_VALUE_OPTIONS}
            selected={tripValues}
            onToggle={(item) => toggleValue(item, setTripValues, 4)}
            activeClassName="border-emerald-700 bg-emerald-700"
            maxSelections={4}
          />
        </section>

        <section className="grid gap-6">
          <h2 className="text-lg font-semibold text-slate-900">Food filters</h2>

          <ToggleGroup
            title="Dietary preferences"
            subtitle="Used to narrow restaurant suggestions"
            items={DIETARY_OPTIONS}
            selected={dietaryPreferences}
            onToggle={(item) => toggleValue(item, setDietaryPreferences)}
            activeClassName="border-emerald-700 bg-emerald-700"
          />

          <ToggleGroup
            title="Allergies"
            subtitle="Used to avoid risky food recommendations"
            items={ALLERGY_OPTIONS}
            selected={allergies}
            onToggle={(item) => toggleValue(item, setAllergies)}
            activeClassName="border-rose-700 bg-rose-700"
          />

          <ToggleGroup
            title="Preferred meal rhythm"
            subtitle="This helps anchor meals throughout the day"
            items={MEAL_TIME_OPTIONS}
            selected={preferredMealTimes}
            onToggle={(item) => toggleValue(item, setPreferredMealTimes, 4)}
            activeClassName="border-orange-700 bg-orange-700"
            maxSelections={4}
          />
        </section>
      </div>

      <button
        type="button"
        onClick={handleSubmit}
        disabled={loading}
        className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium !text-white transition hover:bg-slate-700 disabled:opacity-50"
      >
        {loading ? "Analyzing..." : "Save Travel Personality"}
      </button>

      {result && (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
            {result.personality_label}
          </p>
          <p className="mt-2 text-slate-700">{result.summary}</p>

          <div className="mt-4">
            <p className="text-sm font-medium text-slate-600">Scores</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {Object.entries(result.scores).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
                >
                  <span className="font-medium capitalize">
                    {key.replaceAll("_", " ")}
                  </span>
                  : {value}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}