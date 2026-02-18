'use client';

import React from 'react'
import Footer from './Footer'

const Layout = ({ children, className = "" }) => {
    return (
        <div className="min-h-screen bg-white flex flex-col">
            <div className={`flex-1 flex flex-col w-full pb-16 ${className}`}>
                {children}
            </div>
            <Footer />
        </div>
    )
}

export default Layout
