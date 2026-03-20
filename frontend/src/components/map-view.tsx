"use client";

import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

type Place = {
  name: string;
  lat?: number | null;
  lng?: number | null;
  category: string;
};

export default function MapView({ places }: { places: Place[] }) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);

  useEffect(() => {
    if (!mapContainer.current || !MAPBOX_TOKEN) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v12",
      center: [139.75, 35.68],
      zoom: 11,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");
    mapRef.current = map;

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
      map.remove();
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    const validPlaces = places.filter(
      (p) => typeof p.lat === "number" && typeof p.lng === "number"
    );

    if (validPlaces.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();

    validPlaces.forEach((place) => {
      const el = document.createElement("div");
      el.style.width = "18px";
      el.style.height = "18px";
      el.style.borderRadius = "9999px";
      el.style.backgroundColor = "#ef4444";
      el.style.border = "3px solid white";
      el.style.boxShadow = "0 4px 10px rgba(0,0,0,0.4)";
      el.style.cursor = "pointer";
      el.style.transition = "transform 0.15s ease";

      el.onmouseenter = () => {
        el.style.transform = "scale(1.2)";
      };

      el.onmouseleave = () => {
        el.style.transform = "scale(1)";
      };

      const marker = new mapboxgl.Marker(el)
        .setLngLat([place.lng as number, place.lat as number])
        .setPopup(
          new mapboxgl.Popup({ offset: 20 }).setHTML(
            `<div style="font-size: 13px; font-weight: 600;">${place.name}</div>
             <div style="font-size: 12px; color: #475569;">${place.category}</div>`
          )
        )
        .addTo(mapRef.current!);

      markersRef.current.push(marker);
      bounds.extend([place.lng as number, place.lat as number]);
    });

    mapRef.current.fitBounds(bounds, { padding: 50, maxZoom: 13 });
  }, [places]);

  if (!MAPBOX_TOKEN) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        Map is unavailable because NEXT_PUBLIC_MAPBOX_TOKEN is missing.
      </div>
    );
  }

  return (
    <div className="relative z-0 overflow-hidden rounded-2xl border border-slate-200">
      <div ref={mapContainer} className="h-[420px] w-full" />
    </div>
  );
}