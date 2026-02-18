/** @type {import('next').NextConfig} */
const nextConfig = {
    // Only recognize .ts and .tsx files for pages, ignoring .jsx files in src/pages
    // This effectively disables Pages Router and uses only App Router
    pageExtensions: ['ts', 'tsx', 'js', 'jsx'],
    output: 'standalone',
    async rewrites() {
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
        return [
            {
                source: '/api/:path*',
                destination: `${backendUrl}/api/:path*`,
            },
            {
                source: '/ws/:path*',
                destination: `${backendUrl}/ws/:path*`,
            },
        ];
    },
};

module.exports = nextConfig;

