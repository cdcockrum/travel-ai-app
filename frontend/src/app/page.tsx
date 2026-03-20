import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-16">
      <div className="mx-auto max-w-5xl">
        <div className="glass-card rounded-3xl border border-slate-200 bg-white/85 p-10 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">
            Travel AI
          </p>
          <h1 className="mt-4 text-5xl font-bold tracking-tight text-slate-950">
            Plan trips with real travel intelligence
          </h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-700">
            Generate neighborhood-aware itineraries, map-ready place selections,
            smarter dining suggestions, and personalized travel guidance in one
            workflow.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/trip-builder"
              className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-medium text-white transition hover:-translate-y-0.5 hover:bg-slate-800"
            >
              Open Trip Builder
            </Link>

            <Link
              href="/quiz"
              className="rounded-2xl border border-slate-300 bg-white px-6 py-3 text-sm font-medium text-slate-800 transition hover:-translate-y-0.5 hover:bg-slate-50"
            >
              Traveler Quiz
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}