'use client'

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

interface GlobalMapProps {
  countryStats: Array<{
    country_id: number
    country_name: string
    iso_code: string
    total_cases: number
    latitude?: number
    longitude?: number
  }>
}

export default function GlobalMap({ countryStats }: GlobalMapProps) {
  const getRadius = (cases: number) => {
    return Math.max(4, Math.log10(cases || 1) * 3)
  }

  const getColor = (cases: number) => {
    if (cases > 100000) return '#ef4444' // red-500
    if (cases > 10000) return '#f97316' // orange-500
    if (cases > 1000) return '#eab308' // yellow-500
    return '#3b82f6' // blue-500
  }

  return (
    <div className="h-[500px] w-full rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-sm relative z-0">
      <MapContainer
        center={[20, 0]}
        zoom={2}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="map-tiles"
        />
        {countryStats.map((country) => {
          if (country.latitude === undefined || country.longitude === undefined) return null
          
          return (
            <CircleMarker
              key={country.country_id}
              center={[country.latitude, country.longitude]}
              radius={getRadius(country.total_cases)}
              pathOptions={{
                color: getColor(country.total_cases),
                fillColor: getColor(country.total_cases),
                fillOpacity: 0.6,
                weight: 1
              }}
            >
              <Popup>
                <div className="font-semibold text-slate-900">{country.country_name}</div>
                <div className="text-slate-600">Total Cases: {country.total_cases.toLocaleString()}</div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
      
      <style jsx global>{`
        .dark .map-tiles {
          filter: brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3) brightness(0.7);
        }
        .dark .leaflet-container {
          background: #0f172a;
        }
      `}</style>
    </div>
  )
}
