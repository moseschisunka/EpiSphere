'use client'

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useState } from 'react'
import { publicApi } from '../../lib/api'

export default function PublicMap() {
    const [points, setPoints] = useState<any[]>([])

    useEffect(() => {
        publicApi.getMap().then(setPoints).catch(console.error)
    }, [])

    return (
        <div className="h-[400px] w-full bg-gray-100 rounded overflow-hidden relative z-0">
            {typeof window !== 'undefined' && (
                <MapContainer center={[0, 0]} zoom={2} style={{ height: '100%', width: '100%' }}>
                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    {points.map((p, idx) => (
                        <CircleMarker
                            key={idx}
                            center={[p.lat, p.lon]}
                            radius={5}
                            pathOptions={{ color: 'blue', fillColor: 'cyan', fillOpacity: 0.7 }}
                        >
                            <Popup>
                                <strong>{p.name}</strong><br />
                                Visits: {p.count === 0 ? "Low/None" : p.count}
                            </Popup>
                        </CircleMarker>
                    ))}
                </MapContainer>
            )}
        </div>
    )
}
