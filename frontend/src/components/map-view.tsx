"use client";

import React, { useEffect, useMemo, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

type Place = {
  name: string;
  address?: string | null;
  lat?: number | null;
  lng?: number | null;
  category: string;
  google_maps_url?: string | null;
  rating?: number | null;
  day?: number;
};

function categoryBadge(category: string): { label: string; emoji: string } {
  const c = (category || "").toLowerCase();
  if (c.includes("restaurant") || c.includes("food") || c.includes("cafe")) return { label: "Food", emoji: "🍽️" };
  if (c.includes("attraction") || c.includes("museum") || c.includes("park")) return { label: "Attraction", emoji: "📍" };
  if (c.includes("hotel") || c.includes("lodging")) return { label: "Hotel", emoji: "🏨" };
  if (c.includes("event")) return { label: "Event", emoji: "🎟️" };
  return { label: category || "Place", emoji: "🧭" };
}

function markerColor(category: string): string {
  const c = (category || "").toLowerCase();
  if (c.includes("restaurant") || c.includes("food") || c.includes("cafe")) return "#111827"; // slate-900
  if (c.includes("attraction") || c.includes("museum") || c.includes("park")) return "#2563EB"; // blue-600
  if (c.includes("hotel") || c.includes("lodging")) return "#9333EA"; // purple-600
  if (c.includes("event")) return "#DC2626"; // red-600
  return "#0F766E"; // teal-700
}

function isValidCoord(n: unknown): n is number {
  return typeof n === "number" && Number.isFinite(n);
}

export default function MapView({ places }: { places: Place[] }) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);

  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

  const safePlaces = useMemo(() => {
    return (places || []).filter((p) => isValidCoord(p.lat) && isValidCoord(p.lng));
  }, [places]);

  useEffect(() => {
    if (!token) return;
    if (!mapContainerRef.current) return;

    mapboxgl.accessToken = token;

    if (!mapRef.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/streets-v12",
        center: [-98.5795, 39.8283], // USA-ish default
        zoom: 3,
      });

      mapRef.current.addControl(new mapboxgl.NavigationControl(), "top-right");
    }

    return () => {
      // keep map instance; Next.js remounts can cause flicker if we destroy it
    };
  }, [token]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear markers
    for (const m of markersRef.current) m.remove();
    markersRef.current = [];

    if (!safePlaces.length) return;

    const bounds = new mapboxgl.LngLatBounds();

    for (const p of safePlaces) {
      const el = document.createElement("div");
      el.style.width = "14px";
      el.style.height = "14px";
      el.style.borderRadius = "999px";
      el.style.background = markerColor(p.category);
      el.style.border = "2px solid white";
      el.style.boxShadow = "0 2px 8px rgba(0,0,0,0.25)";
      el.style.cursor = "pointer";

      const badge = categoryBadge(p.category);
      const mapsUrl =
        p.google_maps_url ||
        `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(p.name)}`;

      const popupHtml = `
        <div style="min-width:220px; font-family: ui-sans-serif, system-ui;">
          <div style="font-weight:700; margin-bottom:4px;">${badge.emoji} ${escapeHtml(p.name)}</div>
          ${p.address ? `<div style="color:#475569; font-size:12px; margin-bottom:6px;">${escapeHtml(p.address)}</div>` : ""}
          <div style="display:flex; gap:10px; align-items:center; font-size:12px; color:#334155;">
            <span><b>${escapeHtml(badge.label)}</b></span>
            ${p.rating != null ? `<span>⭐ ${p.rating}</span>` : ""}
            ${p.day != null ? `<span>Day ${p.day}</span>` : ""}
          </div>
          <div style="margin-top:10px;">
            <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer"
               style="display:inline-block; padding:8px 10px; border-radius:10px; background:#111827; color:white; text-decoration:none; font-size:12px;">
               Open in Google Maps
            </a>
          </div>
        </div>
      `;

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([p.lng as number, p.lat as number])
        .setPopup(new mapboxgl.Popup({ offset: 18 }).setHTML(popupHtml))
        .addTo(map);

      markersRef.current.push(marker);
      bounds.extend([p.lng as number, p.lat as number]);
    }

    map.fitBounds(bounds, { padding: 60, maxZoom: 13, duration: 500 });
  }, [safePlaces]);

  if (!token) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Missing <code className="font-mono">NEXT_PUBLIC_MAPBOX_TOKEN</code> in your environment variables.
      </div>
    );
  }

  return <div ref={mapContainerRef} className="h-[420px] w-full rounded-2xl border border-slate-200" />;
}

function escapeHtml(input: string): string {
  return input
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}