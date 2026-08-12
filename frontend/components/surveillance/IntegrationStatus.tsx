'use client'

import { useEffect, useState } from 'react'
import { interopApi } from '../../lib/api'

export default function IntegrationStatus() {
    const [logs, setLogs] = useState<any[]>([])

    const refreshLogs = () => {
        interopApi.getLogs().then(setLogs).catch(console.error)
    }

    useEffect(() => {
        refreshLogs()
    }, [])

    return (
        <div className="bg-white p-4 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">DHIS2 Integration Status</h3>
                <span className="text-xs text-gray-500">Validated dispatch is available in Admin Portal</span>
            </div>

            <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-4 py-2 text-left">Time</th>
                            <th className="px-4 py-2 text-left">System</th>
                            <th className="px-4 py-2 text-left">Direction</th>
                            <th className="px-4 py-2 text-left">Dataset</th>
                            <th className="px-4 py-2 text-left">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {logs.map(log => (
                            <tr key={log.id} className="border-t">
                                <td className="px-4 py-2">{new Date(log.timestamp).toLocaleString()}</td>
                                <td className="px-4 py-2">{log.system_name}</td>
                                <td className="px-4 py-2 uppercase text-xs font-bold text-gray-500">{log.direction}</td>
                                <td className="px-4 py-2">{log.dataset_type}</td>
                                <td className="px-4 py-2">
                                    <span className={`px-2 py-1 rounded-full text-xs ${log.status === 'success' ? 'bg-green-100 text-green-800' :
                                            log.status === 'failure' ? 'bg-red-100 text-red-800' : 'bg-gray-100'
                                        }`}>
                                        {log.status}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {logs.length === 0 && <p className="text-gray-500 text-center py-4">No integration logs found.</p>}
            </div>
        </div>
    )
}
