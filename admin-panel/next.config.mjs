/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://kinochi-project-alpha.onrender.com/api/:path*',
      },
    ]
  },
}
export default nextConfig;
