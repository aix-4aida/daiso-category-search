'use client';

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Home, Grid, Map } from 'lucide-react';

const Footer = () => {
    const router = useRouter();
    const pathname = usePathname();

    const tabs = [
        { id: 'home', label: '홈', icon: Home, path: '/' },
        { id: 'category', label: '카테고리', icon: Grid, path: '/Categories' },
        { id: 'map', label: '매장배치도', icon: Map, path: '/Map' },
    ];

    return (
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 pb-safe z-50">
            <div className="flex justify-around items-center h-16">
                {tabs.map((tab) => {
                    // Check if active (simple path check)
                    // For Home, exact match. For others, startsWith
                    const isActive = tab.path === '/'
                        ? pathname === '/'
                        : pathname.startsWith(tab.path);

                    return (
                        <button
                            key={tab.id}
                            onClick={() => router.push(tab.path)}
                            className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${isActive ? 'text-daiso-red' : 'text-gray-400'
                                }`}
                        >
                            <tab.icon size={24} strokeWidth={isActive ? 2.5 : 2} />
                            <span className="text-[10px] font-medium">{tab.label}</span>
                        </button>
                    );
                })}
            </div>
        </nav>
    );
};

export default Footer;

