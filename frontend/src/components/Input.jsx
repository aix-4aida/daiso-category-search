import React, { forwardRef } from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

const Input = forwardRef(({ className, ...props }, ref) => {
    return (
        <input
            className={twMerge(clsx(
                "flex h-12 w-full rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-base ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-daiso-red focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                className
            ))}
            ref={ref}
            {...props}
        />
    )
})

Input.displayName = "Input"

export default Input
