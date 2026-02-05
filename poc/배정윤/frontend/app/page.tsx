"use client";

import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Home() {
  const router = useRouter();
  const [isBlinking, setIsBlinking] = useState(false);

  // Blink animation effect
  useEffect(() => {
    const interval = setInterval(() => {
      setIsBlinking(true);
      setTimeout(() => setIsBlinking(false), 200);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleInteraction = () => {
    // Instant navigation - no delay
    router.push('/search');
  };

  return (
    <main
      className="flex min-h-screen flex-col items-center justify-center bg-gray-900 p-24 cursor-pointer"
      onClick={handleInteraction}
    >
      {/* Prefetch search page for instant loading */}
      <Link href="/search" prefetch={true} className="hidden" />

      <div className="flex flex-col items-center gap-8">
        {/* Robot Face Container */}
        <div className="relative w-64 h-64 bg-blue-500 rounded-3xl shadow-[0_0_50px_rgba(59,130,246,0.5)] flex flex-col justify-center items-center transition-transform hover:scale-105 duration-300">

          {/* Eyes */}
          <div className="flex gap-12">
            <div className={`w-12 h-12 bg-white rounded-full transition-all duration-100 ${isBlinking ? 'h-1 translate-y-6' : ''}`}></div>
            <div className={`w-12 h-12 bg-white rounded-full transition-all duration-100 ${isBlinking ? 'h-1 translate-y-6' : ''}`}></div>
          </div>

          {/* Mouth */}
          <div className="absolute bottom-16 w-16 h-2 bg-white rounded-full opacity-80"></div>

          {/* Antenna */}
          <div className="absolute -top-6 w-2 h-8 bg-gray-400"></div>
          <div className="absolute -top-9 w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
        </div>

        <h1 className="text-4xl font-bold text-white text-center animate-bounce">
          Hi! Need help finding something?
        </h1>
        <p className="text-gray-400 text-xl">Touch screen to start</p>
      </div>
    </main>
  );
}
