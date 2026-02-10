/** @type {import('next').NextConfig} */
const nextConfig = {
    // Only recognize .ts and .tsx files for pages, ignoring .jsx files in src/pages
    // This effectively disables Pages Router and uses only App Router
    pageExtensions: ['ts', 'tsx'],
    output: 'standalone',
};

module.exports = nextConfig;
