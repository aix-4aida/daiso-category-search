import React from 'react'
import Layout from '../components/Layout'
import SimpleMap from '../components/SimpleMap'

const MapPage = () => {
    return (
        <Layout className="bg-white h-screen flex flex-col">
            <header className="p-4 border-b flex items-center justify-center shrink-0">
                <h1 className="text-xl font-bold">매장 배치도</h1>
            </header>

            <div className="flex-1 overflow-hidden p-4">
                <SimpleMap />
            </div>
        </Layout>
    )
}

export default MapPage
