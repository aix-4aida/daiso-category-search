'use client';

import React, { useState } from 'react'
import Layout from '../../components/Layout'

const MapPage = () => {
    const [activeFloor, setActiveFloor] = useState('B1')

    return (
        <Layout className="bg-white">
            <header className="p-4 border-b flex items-center justify-center shrink-0">
                <h1 className="text-xl font-bold">매장 배치도</h1>
            </header>

            {/* Floor Tab Selector */}
            <div className="flex border-b shrink-0">
                {['B1', 'B2'].map((floor) => (
                    <button
                        key={floor}
                        onClick={() => setActiveFloor(floor)}
                        className={`flex-1 py-3 text-base font-bold transition-colors ${activeFloor === floor
                                ? 'text-daiso-red border-b-2 border-daiso-red'
                                : 'text-gray-400'
                            }`}
                    >
                        {floor}층
                    </button>
                ))}
            </div>

            {/* Map Image */}
            <div className="flex-1 overflow-auto p-4 flex items-start justify-center">
                {activeFloor === 'B1' ? (
                    <img
                        src="/map_b1.jpg"
                        alt="B1 매장 배치도"
                        className="max-w-full h-auto rounded-xl shadow-sm border border-gray-100"
                    />
                ) : (
                    <img
                        src="/map_b2.jpg"
                        alt="B2 매장 배치도"
                        className="max-w-full h-auto rounded-xl shadow-sm border border-gray-100"
                    />
                )}
            </div>
        </Layout>
    )
}

export default MapPage
