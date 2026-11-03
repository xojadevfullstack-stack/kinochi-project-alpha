/** @type {import('next').NextConfig} */
const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const apiUrl = rawApiUrl.replace(
  'https://kinochi-project-alpha.onrender.com',
  'https://kinochi-project-alpha-9g6j.onrender.com'
);
const backendBase = apiUrl.replace(/\/api\/v1\/?$/, '');

const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendBase}/api/:path*`,
      },
    ]
  },
}
export default nextConfig;
