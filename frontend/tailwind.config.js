/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                daiso: {
                    red: '#E31937', // Daiso Brand Color
                }
            }
        },
    },
    plugins: [],
}
