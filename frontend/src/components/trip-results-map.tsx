"use client";

import Map, { Marker, NavigationControl, Popup } from "react-map-gl/mapbox";
import { useMemo, useState } from "react";

type MapPoint = {
  name: string;
  category: string;
  lat: number;
  lng: number;
};

function markerLabel(category: string) {
  if (category === "restaurant") return "🍽";
  if (category === "hotel") return "🏨";
  if (category === "highlight") return "📍";
  return "•";
}

export default function TripResultsMap({
  points,
}: {
  points: MapPoint[];
}) {
  const [selected, setSelected] = useState<MapPoint | null>(null);

  const initialView = useMemo(() => {
    const valid = points.filter(
      (p) =>
        typeof p.lat === "number" &&
        !Number.isNaN(p.lat) &&
        typeof p.lng === "number" &&
        !Number.isNaN(p.lng)
    );

    if (!valid.length) {
      return {
        latitude: 35.6762,
        longitude: 139.6503,
        zoom: 10,
      };
    }

    const avgLat = valid.reduce((sum, p) => sum + p.lat, 0) / valid.length;
    const avgLng = valid.reduce((sum, p) => sum + p.lng, 0) / valid.length;

    return {
      latitude: avgLat,
      longitude: avgLng,
      zoom: 11,
    };
  }, [points]);

  if (!points?.length) return null;

  if (!process.env.NEXT_PUBLIC_MAPBOX_TOKEN) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        Map could not load because <code>NEXT_PUBLIC_MAPBOX_TOKEN</code> is missing.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-slate-900">Map</h3>
        <p className="text-sm text-slate-600">
          Restaurants, hotels, and highlights from your trip results.
        </p>
      </div>

      <div className="h-[420px] overflow-hidden rounded-2xl border border-slate-200">
        <Map
          initialViewState={initialView}
          mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN}
          mapStyle="mapbox://styles/mapbox/streets-v12"
          style={{ width: "100%", height: "100%" }}
        >
          <NavigationControl position="top-right" />

          {points.map((point, index) => (
            <Marker
              key={`${point.name}-${index}`}
              latitude={point.lat}
              longitude={point.lng}
              anchor="bottom"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                setSelected(point);
              }}
            >
              <button
                type="button"
                className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-300 bg-white text-base shadow"
                aria-label={point.name}
              >
                {markerLabel(point.category)}
              </button>
            </Marker>
          ))}

          {selected ? (
            <Popup
              latitude={selected.lat}
              longitude={selected.lng}
              anchor="top"
              onClose={() => setSelected(null)}
              closeButton
              closeOnClick={false}
            >
              <div className="pr-4">
                <p className="font-semibold text-slate-900">{selected.name}</p>
                <p className="text-sm capitalize text-slate-600">
                  {selected.category}
                </p>
              </div>
            </Popup>
          ) : null}
        </Map>
      </div>
    </div>
  );
}