"use client";

import { useSearchParams } from 'next/navigation';
import { useEffect, useState, useRef, Suspense } from 'react';

function ARContent() {
    const searchParams = useSearchParams();

    // Target product position
    const tx = parseFloat(searchParams.get('tx') || '10');
    const ty = parseFloat(searchParams.get('ty') || '10');

    // User starting position (kiosk)
    const ux = parseFloat(searchParams.get('ux') || '10');
    const uy = parseFloat(searchParams.get('uy') || '2');

    // Product name for display
    const productName = searchParams.get('name') || 'Target';

    const [deviceHeading, setDeviceHeading] = useState<number | null>(null);
    const [permissionGranted, setPermissionGranted] = useState(false);
    const [showMap, setShowMap] = useState(false);
    const [cameraActive, setCameraActive] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);

    // Calculate distance from user to target
    const dx = tx - ux;
    const dy = ty - uy;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // Calculate target bearing (angle from North)
    // atan2(x, y) gives angle from Y-axis (North) in standard navigation
    // Result: 0° = North, 90° = East, 180° = South, 270° = West
    const targetBearing = ((Math.atan2(dx, dy) * 180 / Math.PI) + 360) % 360;

    // Arrow rotation = Target bearing - Device heading
    // This makes the arrow always point toward the target regardless of phone orientation
    const arrowRotation = deviceHeading !== null
        ? ((targetBearing - deviceHeading) + 360) % 360
        : 0;

    // Request permissions for compass and camera
    const requestAccess = async () => {
        // IMMEDIATELY advance the UI
        setPermissionGranted(true);

        // Then request permissions in background
        // 1. Request DeviceOrientation (Compass) - iOS only
        if (typeof (DeviceOrientationEvent as any).requestPermission === 'function') {
            try {
                const permission = await (DeviceOrientationEvent as any).requestPermission();
                if (permission !== 'granted') {
                    console.warn('Compass permission denied');
                }
            } catch (e) {
                console.error('Compass permission error:', e);
            }
        }

        // 2. Request Camera
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                setCameraActive(true);
            }
        } catch (err) {
            console.error("Camera access failed:", err);
        }
    };

    // Compass listener
    useEffect(() => {
        if (!permissionGranted) return;

        let lastHeading = 0;

        const handleOrientation = (e: DeviceOrientationEvent) => {
            let heading: number;

            // iOS Safari uses webkitCompassHeading
            if ((e as any).webkitCompassHeading !== undefined) {
                heading = (e as any).webkitCompassHeading;
            }
            // Android Chrome uses alpha (but inverted)
            else if (e.alpha !== null) {
                // e.alpha: 0 = North, increases counterclockwise
                // We need: 0 = North, increases clockwise
                heading = (360 - e.alpha) % 360;
            }
            else {
                return; // No compass data
            }

            // Smooth the heading to reduce jitter
            const diff = heading - lastHeading;
            let delta = diff;
            if (diff > 180) delta -= 360;
            if (diff < -180) delta += 360;

            lastHeading = (lastHeading + delta * 0.2 + 360) % 360;
            setDeviceHeading(lastHeading);
        };

        window.addEventListener('deviceorientation', handleOrientation, true);
        return () => window.removeEventListener('deviceorientation', handleOrientation, true);
    }, [permissionGranted]);

    // Cleanup camera on unmount
    useEffect(() => {
        return () => {
            if (videoRef.current?.srcObject) {
                (videoRef.current.srcObject as MediaStream).getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const getDirectionText = (heading: number | null) => {
        if (heading === null) return "Initializing...";
        if (heading < 22.5 || heading >= 337.5) return "N";
        if (heading < 67.5) return "NE";
        if (heading < 112.5) return "E";
        if (heading < 157.5) return "SE";
        if (heading < 202.5) return "S";
        if (heading < 247.5) return "SW";
        if (heading < 292.5) return "W";
        return "NW";
    };

    return (
        <div className="min-h-screen bg-black flex flex-col items-center justify-between relative overflow-hidden">
            {/* Camera Background */}
            <div className="absolute inset-0 z-0">
                <video
                    ref={videoRef}
                    autoPlay
                    muted
                    playsInline
                    className="w-full h-full object-cover"
                />
                {/* Dark overlay if camera not active */}
                {!cameraActive && (
                    <div className="absolute inset-0 bg-gradient-to-b from-gray-900 to-black" />
                )}
            </div>

            {/* Header */}
            <div className="z-10 w-full text-center pt-12 px-4">
                <h1 className="text-white text-2xl font-bold drop-shadow-lg" style={{ textShadow: '0 2px 8px rgba(0,0,0,0.8)' }}>
                    {decodeURIComponent(productName)}
                </h1>
                <div className="flex justify-center gap-2 mt-2">
                    <span className="bg-black/60 text-white px-4 py-1 rounded-full text-sm backdrop-blur-md border border-white/20">
                        ~{Math.round(distance)}m away
                    </span>
                    <button
                        onClick={() => setShowMap(!showMap)}
                        className="bg-white text-blue-900 px-4 py-1 rounded-full text-sm font-bold shadow-lg active:scale-95"
                    >
                        {showMap ? '✕ Close' : '🗺️ Map'}
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="z-10 flex-1 flex items-center justify-center w-full p-8">
                {showMap ? (
                    /* Map Overlay */
                    <div className="bg-white p-4 rounded-xl shadow-2xl max-w-sm w-full">
                        <h3 className="text-black font-bold mb-2 text-center">Store Map</h3>
                        <div className="w-full h-64 bg-gray-100 rounded-lg relative overflow-hidden border border-gray-300">
                            <img
                                src="/daiso_map_category_homeplus-sangbong.jpg"
                                alt="Store Map"
                                className="w-full h-full object-contain"
                            />

                            {/* User Position (Blue) */}
                            <div
                                className="absolute w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-lg z-10 animate-pulse"
                                style={{
                                    left: `${(ux / 20) * 100}%`,
                                    bottom: `${(uy / 20) * 100}%`,
                                    transform: 'translate(-50%, 50%)'
                                }}
                            />

                            {/* Target Position (Red) */}
                            <div
                                className="absolute w-6 h-6 bg-red-600 rounded-full border-2 border-white shadow-lg z-10 flex items-center justify-center"
                                style={{
                                    left: `${(tx / 20) * 100}%`,
                                    bottom: `${(ty / 20) * 100}%`,
                                    transform: 'translate(-50%, 50%)'
                                }}
                            >
                                <span className="text-white text-xs">★</span>
                            </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-2 text-center">
                            🔵 You (Kiosk) → 🔴 Target
                        </p>
                    </div>
                ) : !permissionGranted ? (
                    /* Permission Request */
                    <div className="flex flex-col items-center gap-6 text-center px-8">
                        <div className="w-24 h-24 bg-blue-600/30 rounded-full flex items-center justify-center animate-pulse">
                            <span className="text-5xl">📱</span>
                        </div>
                        <p className="text-white text-lg">
                            Tap below to start AR Navigation
                        </p>
                        <button
                            onClick={requestAccess}
                            className="bg-blue-600 text-white px-10 py-5 rounded-full font-bold shadow-lg text-xl active:scale-95 transition-transform"
                        >
                            Start Camera & Compass
                        </button>
                        <p className="text-gray-500 text-xs">
                            Requires HTTPS. Use Chrome or Safari.
                        </p>
                    </div>
                ) : (
                    /* AR Navigation Arrow */
                    <div
                        className="transition-transform duration-150 ease-out"
                        style={{ transform: `rotate(${arrowRotation}deg)` }}
                    >
                        {/* Airplane/Navigation Arrow SVG */}
                        <svg
                            width="280"
                            height="280"
                            viewBox="0 0 100 100"
                            style={{ filter: 'drop-shadow(0 10px 20px rgba(0,0,0,0.5))' }}
                        >
                            {/* Outer Circle */}
                            <circle cx="50" cy="50" r="48" fill="rgba(0,0,0,0.3)" stroke="white" strokeWidth="2" />

                            {/* Navigation Arrow (Airplane shape pointing UP) */}
                            <path
                                d="M50 10 L35 75 L50 65 L65 75 Z"
                                fill="#00FF00"
                                stroke="white"
                                strokeWidth="3"
                                strokeLinejoin="round"
                            />

                            {/* Center dot */}
                            <circle cx="50" cy="50" r="4" fill="white" />
                        </svg>
                    </div>
                )}
            </div>

            {/* Footer Info */}
            <div className="z-10 bg-black/70 p-4 rounded-t-2xl text-white text-center backdrop-blur-md w-full border-t border-white/10">
                <div className="flex justify-center items-center gap-4">
                    <div className="text-left">
                        <p className="text-xs text-gray-400">Heading</p>
                        <p className="text-2xl font-mono font-bold text-yellow-400">
                            {deviceHeading !== null ? `${Math.round(deviceHeading)}°` : '--°'} {getDirectionText(deviceHeading)}
                        </p>
                    </div>
                    <div className="w-px h-10 bg-gray-600" />
                    <div className="text-left">
                        <p className="text-xs text-gray-400">Target Bearing</p>
                        <p className="text-2xl font-mono font-bold text-green-400">
                            {Math.round(targetBearing)}°
                        </p>
                    </div>
                </div>
                <p className="text-xs text-gray-400 mt-2">
                    {deviceHeading === null && permissionGranted ? "Move phone in figure-8 to calibrate" : "Walk toward the arrow direction"}
                </p>
            </div>
        </div>
    );
}

export default function ARPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-black text-white flex items-center justify-center">
                <div className="animate-spin text-4xl">🧭</div>
            </div>
        }>
            <ARContent />
        </Suspense>
    );
}
