import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import VoiceSearch from './pages/VoiceSearch'
import SearchResults from './pages/SearchResults'
import MapNavigation from './pages/MapNavigation'
import NoResult from './pages/NoResult'

function App() {
    return (
        <div className="min-h-screen bg-gray-50">
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/search/voice" element={<VoiceSearch />} />
                <Route path="/search/results" element={<SearchResults />} />
                <Route path="/map" element={<MapNavigation />} />
                <Route path="/search/fail" element={<NoResult />} />
            </Routes>
        </div>
    )
}

export default App
