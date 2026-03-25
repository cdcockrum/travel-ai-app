import type { Metadata } from "next";
import "./globals.css";
import "mapbox-gl/dist/mapbox-gl.css";

export const metadata: Metadata = {
  title: "AI Travel Intelligence Platform",
  description: "Smarter trip planning with itinerary, maps, weather, and recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}