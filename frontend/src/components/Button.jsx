import React from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

const Button = ({
    children,
    variant = 'primary',
    size = 'md',
    className,
    ...props
}) => {
    const baseStyles = "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none"

    const variants = {
        primary: "bg-daiso-red text-white hover:bg-red-700 focus:ring-red-500",
        secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500",
        ghost: "bg-transparent hover:bg-gray-100 text-gray-700 focus:ring-gray-500",
        outline: "border border-gray-300 bg-transparent hover:bg-gray-50 text-gray-700"
    }

    const sizes = {
        sm: "h-9 px-3 text-sm",
        md: "h-11 px-4 text-base",
        lg: "h-14 px-8 text-lg"
    }

    return (
        <button
            className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
            {...props}
        >
            {children}
        </button>
    )
}

export default Button
