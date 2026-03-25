"use client";

import React, { useEffect, useMemo, useRef } from "react";
import Map, { Marker, NavigationControl, type MapRef } from "react-map-gl/mapbox";
// ✅ IMPORTANT: mapbox entrypoint (prevents maplibre-gl dependency)
import "mapbox-gl/dist/mapbox-gl.css";

type Place = {
  name: string;
  lat: number;
  lng: number;
  category?: string;
  google_maps_url?: string | null;
  day?: number;
  order?: number; // number marker (optional)
};

export default function MapView({ places }: { places: Place[] }) {
  const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  const mapRef = useRef<MapRef | null>(null);

  const validPlaces = useMemo(
    () =>
      (places || []).filter(
        (p) => typeof p.lat === "number" && typeof p.lng === "number"
      ),
    [places]
  );

  const initialView = useMemo(() => {
    if (!validPlaces.length) {
      return { latitude: 41.8781, longitude: -87.6298, zoom: 11 };
    }
    const lat = validPlaces.reduce((s, p) => s + p.lat, 0) / validPlaces.length;
    const lng = validPlaces.reduce((s, p) => s + p.lng, 0) / validPlaces.length;
    return { latitude: lat, longitude: lng, zoom: 12 };
  }, [validPlaces]);

  useEffect(() => {
    if (!mapRef.current) return;
    if (validPlaces.length < 2) return;

    const lats = validPlaces.map((p) => p.lat);
    const lngs = validPlaces.map((p) => p.lng);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    mapRef.current.fitBounds(
      [
        [minLng, minLat],
        [maxLng, maxLat],
      ],
      { padding: 60, duration: 500 }
    );
  }, [validPlaces]);

  if (!mapboxToken) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
        Missing <code className="font-mono">NEXT_PUBLIC_MAPBOX_TOKEN</code> in{" "}
        <code className="font-mono">frontend/.env.local</code>.
      </div>
    );
  }

  return (
    <div className="h-[420px] w-full overflow-hidden rounded-2xl border border-slate-200">
      <Map
        ref={mapRef}
        mapboxAccessToken={mapboxToken}
        initialViewState={initialView}
        mapStyle="mapbox://styles/mapbox/streets-v12"
      >
        <NavigationControl position="top-right" />

        {validPlaces.map((p, idx) => {
          const label = typeof p.order === "number" ? p.order : null;

          return (
            <Marker
              key={`${p.lat}-${p.lng}-${idx}`}
              longitude={p.lng}
              latitude={p.lat}
              anchor="bottom"
            >
              <button
                type="button"
                className="group"
                title={p.name}
                onClick={() => {
                  if (p.google_maps_url) {
                    window.open(p.google_maps_url, "_blank", "noreferrer");
                  }
                }}
              >
                {label ? (
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white shadow-sm ring-2 ring-white">
                    {label}
                  </div>
                ) : (
                  <div className="h-3 w-3 rounded-full bg-slate-900 shadow-sm ring-2 ring-white" />
                )}

                <div className="pointer-events-none mt-2 hidden max-w-[220px] rounded-lg border border-slate-200 bg-white px-2 py-1 text-left text-xs text-slate-800 shadow-sm group-hover:block">
                  <div className="font-medium">{p.name}</div>
                  {p.category ? <div className="text-slate-600">{p.category}</div> : null}
                </div>
              </button>
            </Marker>
          );
        })}
      </Map>
    </div>
  );
}