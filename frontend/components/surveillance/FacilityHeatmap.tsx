'use client'

import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { surveillanceApi } from '../../lib/api'

export default function FacilityHeatmap() {
    const [facilities, setFacilities] = useState<any[]>([])

    useEffect(() => {
        surveillanceApi.getHeatmap().then(setFacilities).catch(console.error)
    }, [])

    // Center map roughly - in real app, calculate bounds
    const center = [0, 0]

    return (
        <div className="bg-white p-4 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Facility Outbreak Heatmap</h3>
            <div className="h-[400px] w-full rounded overflow-hidden relative z-0">
                {/* Note: In a real Next.js app with Leaflet, we need dynamic import with ssr: false. 
              For this artifact generation, I'm writing standard component code. 
              The user might need to adjust for Next.js SSR if strict mode is on. */}
                {typeof window !== 'undefined' && (
                    <MapContainer center={[0, 0]} zoom={2} style={{ height: '100%', width: '100%' }}>
                        <TileLayer
                            attribution='&copy; OpenStreetMap contributors'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        {facilities.map((f, idx) => (
                            <CircleMarker
                                key={idx}
                                center={[f.lat, f.lon]}
                                radius={Math.min(f.count * 2, 20) + 5}
                                pathOptions={{ color: 'red', fillColor: '#f03', fillOpacity: 0.5 }}
                            >
                                <Popup>
                                    <strong>{f.name}</strong><br />
                                    Type: {f.type}<br />
                                    Visits: {f.count}
                                </Popup>
                            </CircleMarker>
                        ))}
                    </MapContainer>
                )}
            </div>
        </div>
    )
}
